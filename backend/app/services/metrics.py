from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.asistencia import ESTADOS_ASISTENCIA, SesionClase
from app.models.sede import Grupo, Sede
from app.models.student import Student
from app.models.user import User

MANAGER_ROLES = ("admin", "coordinador", "subcoordinador")
ATENDIDAS = ("asistio", "retardo", "cubierta")
MARCADAS = ("asistio", "retardo", "falta", "justificada", "cubierta")
STATUS_LABELS = {
    "pendiente": "Pendiente",
    "asistio": "Asistió",
    "retardo": "Retardo",
    "falta": "Falta",
    "justificada": "Justificada",
    "cancelada": "Cancelada",
    "cubierta": "Cubierta",
}


def _full_name(user: User | None) -> str:
    if user is None:
        return "Sin asignar"
    return f"{user.nombre} {user.apellido_paterno} {user.apellido_materno or ''}".strip()


def _today() -> date:
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()


def _sede_ids(user: User, requested_sede_id: int | None) -> list[int] | None:
    if user.role == "admin":
        return [requested_sede_id] if requested_sede_id is not None else None
    if user.role in ("coordinador", "subcoordinador"):
        if user.sede_id is None:
            raise ValueError("Usuario sin sede asignada")
        if requested_sede_id is not None and requested_sede_id != user.sede_id:
            raise ValueError("No autorizado para esta sede")
        return [user.sede_id]
    return None


def _week_start(day: date) -> date:
    return day - timedelta(days=day.isoweekday() - 1)


def _empty_counts() -> dict[str, int]:
    return {estado: 0 for estado in ESTADOS_ASISTENCIA}


async def build_metrics(
    db: AsyncSession,
    user: User,
    desde: date | None = None,
    hasta: date | None = None,
    sede_id: int | None = None,
) -> dict:
    today = _today()
    start = desde or (today - timedelta(days=42))
    end = hasta or (today + timedelta(days=14))
    if start > end:
        raise ValueError("El periodo debe tener fecha de inicio menor o igual al fin")
    if user.role not in MANAGER_ROLES and user.role != "tutor":
        raise PermissionError("Rol no autorizado")

    is_tutor = user.role == "tutor"
    sede_scope = _sede_ids(user, sede_id)

    stmt = select(SesionClase).where(SesionClase.fecha >= start, SesionClase.fecha <= end)
    if is_tutor:
        stmt = stmt.where(or_(SesionClase.tutor_id == user.id, SesionClase.tutor_cubridor_id == user.id))
    elif sede_scope is not None:
        stmt = stmt.where(SesionClase.sede_id.in_(sede_scope))
    sessions = (await db.execute(stmt.order_by(SesionClase.fecha, SesionClase.hora_inicio))).scalars().all()

    counts = _empty_counts()
    weeks: dict[date, dict[str, int]] = defaultdict(_empty_counts)
    by_sede: dict[int, dict[str, int]] = defaultdict(_empty_counts)
    workload: dict[int, dict[str, int]] = defaultdict(lambda: {"asignadas": 0, "impartidas": 0, "faltas": 0, "cubiertas": 0})
    user_ids = set()
    own_impartidas = own_marked = own_attended = 0
    for session in sessions:
        counts[session.estado] += 1
        week = _week_start(session.fecha)
        weeks[week][session.estado] += 1
        by_sede[session.sede_id][session.estado] += 1
        if is_tutor:
            if session.tutor_id == user.id and session.estado in ("asistio", "retardo"):
                own_impartidas += 1
                own_attended += 1
                own_marked += 1
            elif session.tutor_id == user.id and session.estado in ("falta", "justificada"):
                own_marked += 1
            if session.tutor_cubridor_id == user.id and session.estado == "cubierta":
                own_impartidas += 1
                own_attended += 1
                own_marked += 1
        if not is_tutor:
            user_ids.add(session.tutor_id)
            workload[session.tutor_id]["asignadas"] += 1
            if session.estado in ("asistio", "retardo"):
                workload[session.tutor_id]["impartidas"] += 1
            if session.estado == "falta":
                workload[session.tutor_id]["faltas"] += 1
            if session.tutor_cubridor_id and session.estado == "cubierta":
                user_ids.add(session.tutor_cubridor_id)
                workload[session.tutor_cubridor_id]["cubiertas"] += 1

    marked = own_marked if is_tutor else sum(counts[estado] for estado in MARCADAS)
    attended = own_attended if is_tutor else sum(counts[estado] for estado in ATENDIDAS)
    tasa = round((attended / marked) * 100, 1) if marked else 0.0
    cubiertas = counts["cubierta"]
    faltas = counts["falta"]

    users = {}
    if user_ids:
        users = {u.id: u for u in (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()}
    sedes = {}
    if by_sede:
        sedes = {s.id: s for s in (await db.execute(select(Sede).where(Sede.id.in_(by_sede.keys())))).scalars().all()}

    total_alumnos = total_tutores = total_grupos = 0
    if not is_tutor:
        student_stmt = select(func.count()).select_from(Student).where(Student.deleted_at.is_(None), Student.estatus == "activo")
        tutor_stmt = select(func.count()).select_from(User).where(User.es_tutor == True, User.is_active == True, User.deleted_at.is_(None))  # noqa: E712
        group_stmt = select(func.count()).select_from(Grupo).where(Grupo.deleted_at.is_(None))
        if sede_scope is not None:
            student_stmt = student_stmt.where(Student.sede_id.in_(sede_scope))
            tutor_stmt = tutor_stmt.where(User.sede_id.in_(sede_scope))
            group_stmt = group_stmt.where(Grupo.sede_id.in_(sede_scope))
        total_alumnos = (await db.execute(student_stmt)).scalar_one()
        total_tutores = (await db.execute(tutor_stmt)).scalar_one()
        total_grupos = (await db.execute(group_stmt)).scalar_one()

    if is_tutor:
        kpis = [
            {"id": "impartidas", "label": "Clases impartidas", "value": attended, "hint": "Asistencias, retardos y cubiertas"},
            {"id": "asistio", "label": "Asistencias", "value": counts["asistio"], "hint": "Clases registradas a tiempo"},
            {"id": "retardo", "label": "Retardos", "value": counts["retardo"], "hint": "Llegadas tarde registradas"},
            {"id": "falta", "label": "Faltas", "value": faltas, "hint": "Clases no impartidas"},
            {"id": "cubierta", "label": "Cubiertas", "value": cubiertas, "hint": "Clases que cubriste o te cubrieron"},
            {"id": "pendiente", "label": "Pendientes", "value": counts["pendiente"], "hint": "Sin registro de asistencia"},
        ]
        scope = "personal"
    else:
        kpis = [
            {"id": "alumnos", "label": "Alumnos activos", "value": total_alumnos, "hint": "Estudiantes con estatus activo"},
            {"id": "tutores", "label": "Tutores activos", "value": total_tutores, "hint": "Tutores disponibles en la sede"},
            {"id": "grupos", "label": "Grupos activos", "value": total_grupos, "hint": "Grupos abiertos actualmente"},
            {"id": "sesiones", "label": "Sesiones en periodo", "value": len(sessions), "hint": "Clases programadas y manuales"},
            {"id": "asistencia", "label": "Tasa de asistencia", "value": tasa, "hint": "Porcentaje de clases atendidas", "suffix": "%"},
            {"id": "cubiertas", "label": "Clases cubiertas", "value": cubiertas, "hint": "Sesiones resueltas por otro tutor"},
        ]
        scope = "global" if user.role == "admin" and sede_scope is None else "sede"

    por_semana = []
    for week in sorted(weeks):
        item = weeks[week]
        por_semana.append({
            "semana": week.isoformat(),
            "label": week.strftime("%d/%m"),
            **{estado: item[estado] for estado in ESTADOS_ASISTENCIA},
            "total": sum(item.values()),
            "atendidas": sum(item[estado] for estado in ATENDIDAS),
        })

    por_estado = [
        {"estado": estado, "label": STATUS_LABELS[estado], "total": counts[estado]}
        for estado in ESTADOS_ASISTENCIA
    ]

    por_sede = []
    for sede_key, item in by_sede.items():
        sede = sedes.get(sede_key)
        total = sum(item.values())
        marcadas = sum(item[estado] for estado in MARCADAS)
        atendidas = sum(item[estado] for estado in ATENDIDAS)
        por_sede.append({
            "sede_id": sede_key,
            "sede": sede.nombre if sede else f"Sede {sede_key}",
            "total": total,
            "atendidas": atendidas,
            "faltas": item["falta"],
            "cubiertas": item["cubierta"],
            "pendientes": item["pendiente"],
            "tasa": round((atendidas / marcadas) * 100, 1) if marcadas else 0.0,
        })
    por_sede.sort(key=lambda item: item["total"], reverse=True)

    carga_tutores = []
    if not is_tutor:
        for tutor_key, item in workload.items():
            tutor = users.get(tutor_key)
            carga_tutores.append({
                "tutor_id": tutor_key,
                "tutor": _full_name(tutor),
                **item,
                "total": item["asignadas"],
            })
        carga_tutores.sort(key=lambda item: (item["impartidas"], item["asignadas"]), reverse=True)
        carga_tutores = carga_tutores[:10]

    proximas = []
    if is_tutor:
        upcoming_stmt = (
            select(SesionClase)
            .where(
                or_(SesionClase.tutor_id == user.id, SesionClase.tutor_cubridor_id == user.id),
                SesionClase.fecha >= today,
                SesionClase.estado.in_(("pendiente", "cubierta")),
            )
            .order_by(SesionClase.fecha, SesionClase.hora_inicio)
            .limit(5)
        )
        upcoming = (await db.execute(upcoming_stmt)).scalars().all()
        group_ids = {session.grupo_id for session in upcoming}
        groups = {}
        if group_ids:
            groups = {g.id: g for g in (await db.execute(select(Grupo).where(Grupo.id.in_(group_ids)))).scalars().all()}
        for session in upcoming:
            group = groups.get(session.grupo_id)
            proximas.append({
                "id": session.id,
                "fecha": session.fecha.isoformat(),
                "hora_inicio": session.hora_inicio.strftime("%H:%M"),
                "hora_fin": session.hora_fin.strftime("%H:%M"),
                "grupo": group.nombre if group else f"Grupo {session.grupo_id}",
                "estado": session.estado,
                "rol": "cubridor" if session.tutor_cubridor_id == user.id and session.estado == "cubierta" else "titular",
            })

    return {
        "rol": user.role,
        "alcance": scope,
        "periodo": {"desde": start.isoformat(), "hasta": end.isoformat()},
        "kpis": kpis,
        "asistencia": {
            "por_estado": por_estado,
            "por_semana": por_semana,
            "por_sede": por_sede,
        },
        "carga_tutores": carga_tutores,
        "proximas": proximas,
        "resumen": {
            "total": len(sessions),
            "atendidas": attended,
            "marcadas": marked,
            "tasa": tasa,
            **counts,
        },
    }
