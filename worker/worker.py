import os
import time
import logging
from dotenv import load_dotenv
import httpx
from ortools.sat.python import cp_model

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
WORKER_API_KEY = os.getenv("WORKER_API_KEY", "dev-worker-key")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))
SOLVER_TIMEOUT = int(os.getenv("SOLVER_TIMEOUT", "300"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cuep-worker")

HEADERS = {"X-Worker-Key": WORKER_API_KEY}


def _time_to_hour(t: str) -> int:
    h, m = t.split(":")
    return int(h) + (1 if int(m) >= 30 else 0)


def solve_corrida(data: dict) -> dict:
    tutores = data.get("tutores", [])
    grupos = data.get("grupos", [])
    parametros = data.get("parametros", {}) or {}
    max_horas = parametros.get("max_horas_tutor", 12)

    # authorized materias per tutor
    auth = {}
    roles = {}
    for t in tutores:
        roles[t["id"]] = t.get("role", "tutor")
        auth[t["id"]] = {
            m["materia_id"]: m.get("pref", 1)
            for m in t.get("materias", [])
            if not m.get("vetada", False)
        }

    # availability intervals per tutor as set of hours
    avail_hours = {}
    for t in tutores:
        s = set()
        for d in t.get("disponibilidad", []):
            start = _time_to_hour(d["inicio"])
            end = _time_to_hour(d["fin"])
            for h in range(start, end):
                s.add((d["dia"], h))
        avail_hours[t["id"]] = s

    # CUEP day/range configuration. Fall back to the legacy weekdays if absent.
    configured = data.get("horario_cuep") or []
    day_ranges = []
    for item in configured:
        if not item.get("activo"):
            continue
        day_ranges.append((int(item["dia"]), _time_to_hour(item["inicio"]), _time_to_hour(item["fin"])))
    if not day_ranges:
        day_ranges = [(d, 7, 21) for d in range(1, 7)]
    active_days = sorted({d for d, _, _ in day_ranges})
    day_bounds = {d: (min(s for dd, s, _ in day_ranges if dd == d), max(e for dd, _, e in day_ranges if dd == d)) for d in active_days}

    model = cp_model.CpModel()
    # x[(g,t,d,start)] bool
    x = {}
    for g in grupos:
        for t in tutores:
            if g["materia_id"] not in auth.get(t["id"], {}):
                continue
            nblocks = g["horas_totales"] // g["bloque"]
            for d, day_start, day_end in day_ranges:
                for start in range(day_start, day_end - g["bloque"] + 1):
                    # check availability for all hours of block
                    ok = True
                    for h in range(start, start + g["bloque"]):
                        if (d, h) not in avail_hours[t["id"]]:
                            ok = False
                            break
                    if not ok:
                        continue
                    x[(g["id"], t["id"], d, start)] = model.NewBoolVar(f"x_{g['id']}_{t['id']}_{d}_{start}")

    # each group exactly nblocks assignments
    for g in grupos:
        nblocks = g["horas_totales"] // g["bloque"]
        vars_g = [v for (gg, tt, dd, ss), v in x.items() if gg == g["id"]]
        if not vars_g and nblocks > 0:
            return {"status": "INFEASIBLE", "asignaciones": [], "metricas": {}}
        model.Add(sum(vars_g) == nblocks)

    # tutor no overlap per day/hour
    for t in tutores:
        for d in active_days:
            day_start, day_end = day_bounds[d]
            for hour in range(day_start, day_end):
                covering = []
                for g in grupos:
                    for start in range(hour - g["bloque"] + 1, hour + 1):
                        if (g["id"], t["id"], d, start) in x:
                            covering.append(x[(g["id"], t["id"], d, start)])
                if covering:
                    model.Add(sum(covering) <= 1)

    # carga maxima
    for t in tutores:
        limit = t.get("carga_max") or max_horas
        model.Add(sum(v * next(g["bloque"] for g in grupos if g["id"] == gg) for (gg, tt, dd, ss), v in x.items() if tt == t["id"]) <= limit)

    # objective: preferencia
    obj_terms = []
    for (g_id, t_id, d, s), v in x.items():
        g = next(gg for gg in grupos if gg["id"] == g_id)
        pref = auth[t_id].get(g["materia_id"], 1)
        weight = 10 if pref == 1 else (5 if pref == 2 else 1)
        if roles.get(t_id) in ("coordinador", "subcoordinador"):
            weight = max(1, weight - 4)
        obj_terms.append(weight * v)
    model.Maximize(sum(obj_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SOLVER_TIMEOUT
    solver.parameters.num_search_workers = os.cpu_count() or 4
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "INFEASIBLE", "asignaciones": [], "metricas": {}}

    asignaciones = []
    pref1 = 0
    for (g_id, t_id, d, s), v in x.items():
        if solver.Value(v) == 1:
            g = next(gg for gg in grupos if gg["id"] == g_id)
            asignaciones.append({
                "grupo_id": g_id,
                "tutor_id": t_id,
                "dia": d,
                "hora_inicio": f"{s:02d}:00",
                "hora_fin": f"{s + g['bloque']:02d}:00",
            })
            t = next(tt for tt in tutores if tt["id"] == t_id)
            if auth[t_id].get(g["materia_id"], 1) == 1:
                pref1 += 1

    metricas = {
        "preferencia_1": pref1,
        "asignaciones": len(asignaciones),
        "tiempo_solver_s": solver.WallTime(),
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
    }
    return {"status": metricas["status"], "asignaciones": asignaciones, "metricas": metricas}


def poll_once():
    try:
        r = httpx.get(f"{API_BASE_URL}/worker/tareas", params={"estado": "PENDIENTE", "limit": 1}, headers=HEADERS, timeout=10)
        r.raise_for_status()
        tasks = r.json()
    except Exception as e:
        log.warning("poll error: %s", e)
        return
    if not tasks:
        return
    task = tasks[0]
    tid = task["id"]
    log.info("tarea tomada: %s", tid)
    try:
        httpx.post(f"{API_BASE_URL}/worker/tareas/{tid}/iniciar", headers=HEADERS, timeout=10).raise_for_status()
        httpx.post(f"{API_BASE_URL}/worker/tareas/{tid}/progreso", json={"progreso": 10, "etapa": "Resolviendo con CP-SAT"}, headers=HEADERS, timeout=10)
    except Exception as e:
        log.warning("iniciar error: %s", e)
        return

    data = task.get("parametros_resumen") or {}
    inicio = time.perf_counter()
    try:
        result = solve_corrida(data)
        elapsed = time.perf_counter() - inicio
        metricas = result.get("metricas", {})
        metricas["tiempo_solver_s"] = round(elapsed, 3)
        payload = {
            "estado": "COMPLETADO" if result["status"] in ("OPTIMAL", "FEASIBLE") else "ERROR",
            "resultado_json": {"asignaciones": result.get("asignaciones", [])},
            "metricas_optimizacion": metricas,
        }
        httpx.post(f"{API_BASE_URL}/worker/tareas/{tid}/progreso", json={"progreso": 100, "etapa": "Completado"}, headers=HEADERS, timeout=10)
        if result["status"] not in ("OPTIMAL", "FEASIBLE"):
            httpx.post(f"{API_BASE_URL}/worker/tareas/{tid}/error", json={"detalle": result["status"]}, headers=HEADERS, timeout=10)
        else:
            httpx.post(f"{API_BASE_URL}/worker/tareas/{tid}/resultado", json=payload, headers=HEADERS, timeout=30).raise_for_status()
        log.info("tarea %s -> %s", tid, result["status"])
    except Exception as e:
        log.exception("error resolviendo tarea %s: %s", tid, e)
        try:
            httpx.post(f"{API_BASE_URL}/worker/tareas/{tid}/error", json={"detalle": str(e)}, headers=HEADERS, timeout=10)
        except Exception:
            pass


def main():
    log.info("worker iniciado, api=%s", API_BASE_URL)
    while True:
        poll_once()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
