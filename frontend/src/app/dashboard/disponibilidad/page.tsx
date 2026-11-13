"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/ui/empty-state";

interface Materia { id: number; nombre: string; nivel: string; area: string; }
interface HorarioDia { dia: number; activo: boolean; inicio: string; fin: string; }
interface DisponibilidadItem { dia_semana: number; hora_inicio: string; hora_fin: string; }
interface TutorConfig {
  disponibilidad: DisponibilidadItem[];
  materias: { materia_id: number; nivel_preferencia: number; vetada: boolean }[];
}
interface Interval { inicio: string; fin: string; }

const DAY_LABELS: Record<number, string> = {
  1: "Lunes",
  2: "Martes",
  3: "Miércoles",
  4: "Jueves",
  5: "Viernes",
  6: "Sábado",
  7: "Domingo",
};

function nextHour(value: string) {
  const hour = Number(value.split(":")[0]);
  return `${String(Math.min(hour + 1, 23)).padStart(2, "0")}:00`;
}

export default function DisponibilidadPage() {
  const user = useAuthStore((s) => s.user);
  const { data: materias } = useQuery<Materia[]>({ queryKey: ["materias"], queryFn: async () => (await api.get("/materias")).data });
  const { data: horario, isLoading: loadingHorario } = useQuery<HorarioDia[]>({
    queryKey: ["horario-cuep"],
    queryFn: async () => (await api.get("/configuracion-horario")).data,
  });
  const { data: config, isLoading: loadingConfig } = useQuery<TutorConfig>({
    queryKey: ["tutor-disponibilidad", user?.id],
    queryFn: async () => (await api.get(`/tutores/${user?.id}/disponibilidad`)).data,
    enabled: Boolean(user?.id),
  });

  const [intervals, setIntervals] = useState<Record<number, Interval[]>>({});
  const [materiaSearch, setMateriaSearch] = useState("");
  const [materiaNivel, setMateriaNivel] = useState("");
  const [materiaSort, setMateriaSort] = useState("nombre-asc");
  const [selected, setSelected] = useState<Record<number, { pref: number; vetada: boolean }>>({});
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  const activeDays = useMemo(() => (horario || []).filter((day) => day.activo), [horario]);
  const configByDay = useMemo(() => new Map((horario || []).map((day) => [day.dia, day])), [horario]);

  useEffect(() => {
    if (!horario || !config) return;
    const next: Record<number, Interval[]> = {};
    for (const day of horario) {
      if (day.activo) next[day.dia] = [];
    }
    for (const item of config.disponibilidad) {
      if (next[item.dia_semana]) {
        next[item.dia_semana].push({ inicio: item.hora_inicio, fin: item.hora_fin });
      }
    }
    setIntervals(next);
    setSelected(
      Object.fromEntries(
        config.materias.map((materia) => [materia.materia_id, { pref: materia.nivel_preferencia, vetada: materia.vetada }]),
      ),
    );
  }, [horario, config]);

  const filteredMaterias = useMemo(() => {
    const term = materiaSearch.trim().toLocaleLowerCase("es");
    const list = (materias || []).filter((materia) => {
      if (materiaNivel && materia.nivel !== materiaNivel) return false;
      if (!term) return true;
      return [materia.nombre, materia.area, materia.nivel]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("es")
        .includes(term);
    });
    return [...list].sort((a, b) => {
      if (materiaSort === "nombre-desc") return b.nombre.localeCompare(a.nombre, "es");
      if (materiaSort === "nivel-asc") return a.nivel.localeCompare(b.nivel, "es") || a.nombre.localeCompare(b.nombre, "es");
      if (materiaSort === "area-asc") return a.area.localeCompare(b.area, "es") || a.nombre.localeCompare(b.nombre, "es");
      return a.nombre.localeCompare(b.nombre, "es");
    });
  }, [materias, materiaSearch, materiaNivel, materiaSort]);

  function addBlock(day: number) {
    const window = configByDay.get(day);
    if (!window) return;
    setIntervals((current) => ({
      ...current,
      [day]: [...(current[day] || []), { inicio: window.inicio, fin: nextHour(window.inicio) }],
    }));
  }

  function updateBlock(day: number, index: number, field: keyof Interval, value: string) {
    setIntervals((current) => ({
      ...current,
      [day]: (current[day] || []).map((item, itemIndex) => (itemIndex === index ? { ...item, [field]: value } : item)),
    }));
  }

  function removeBlock(day: number, index: number) {
    setIntervals((current) => ({
      ...current,
      [day]: (current[day] || []).filter((_, itemIndex) => itemIndex !== index),
    }));
  }

  function validate() {
    for (const day of activeDays) {
      const blocks = intervals[day.dia] || [];
      const sorted = [...blocks].sort((a, b) => a.inicio.localeCompare(b.inicio));
      for (let index = 0; index < sorted.length; index += 1) {
        const block = sorted[index];
        if (block.inicio >= block.fin) return `El bloque de ${DAY_LABELS[day.dia]} no es válido.`;
        if (block.inicio < day.inicio || block.fin > day.fin) {
          return `El bloque de ${DAY_LABELS[day.dia]} debe estar entre ${day.inicio} y ${day.fin}.`;
        }
        if (block.inicio.split(":")[1] !== "00" || block.fin.split(":")[1] !== "00") {
          return "Los bloques deben ser en horas completas.";
        }
        if (index + 1 < sorted.length && block.fin > sorted[index + 1].inicio) {
          return `Hay bloques traslapados el ${DAY_LABELS[day.dia]}.`;
        }
      }
    }
    return "";
  }

  async function save() {
    if (!user) return;
    const error = validate();
    if (error) {
      setMsg(error);
      return;
    }
    setSaving(true);
    setMsg("");
    const disponibilidad = activeDays.flatMap((day) =>
      (intervals[day.dia] || []).map((block) => ({
        dia_semana: day.dia,
        hora_inicio: block.inicio,
        hora_fin: block.fin,
      })),
    );
    const materiasPayload = Object.entries(selected).map(([id, value]) => ({
      materia_id: Number(id),
      nivel_preferencia: value.pref,
      vetada: value.vetada,
    }));
    try {
      await api.put(`/tutores/${user.id}/disponibilidad`, { disponibilidad, materias: materiasPayload });
      setMsg("Disponibilidad guardada correctamente.");
    } catch {
      setMsg("No pudimos guardar tu disponibilidad. Revisa los bloques e inténtalo de nuevo.");
    } finally {
      setSaving(false);
    }
  }

  const loading = loadingHorario || loadingConfig;

  return (
    <AppShell title="Disponibilidad">
      <div className="space-y-6">
        <PageHeader title="Disponibilidad y materias" description="Marca cuándo puedes dar asesoría y qué materias quieres acompañar." />

        <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="poster-card h-fit p-5 sm:p-6">
            <p className="type-kicker">Horario base</p>
            <h2 className="mt-2 font-display text-2xl uppercase text-primary">Días y horas</h2>
            <p className="mt-2 text-xs leading-relaxed text-ink/55">
              El CUEP opera en: {activeDays.length ? activeDays.map((day) => `${DAY_LABELS[day.dia]} ${day.inicio}–${day.fin}`).join(" · ") : "sin días configurados"}.
            </p>

            <div className="mt-4 space-y-3">
              {loading && <div className="h-40 animate-pulse border border-ink/15 bg-sand" />}
              {!loading && activeDays.length === 0 && (
                <EmptyState title="Sin horario CUEP" description="La coordinación aún no ha configurado los días y horas del CUEP." />
              )}
              {!loading && activeDays.map((day) => {
                const blocks = intervals[day.dia] || [];
                return (
                  <div key={day.dia} className="border border-ink/20 bg-accent/5 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-display text-xl uppercase text-ink">{DAY_LABELS[day.dia]}</p>
                        <p className="font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">
                          Ventana CUEP: {day.inicio}–{day.fin}
                        </p>
                      </div>
                      <Button type="button" size="sm" variant="outline" onClick={() => addBlock(day.dia)}>
                        Agregar bloque
                      </Button>
                    </div>
                    {blocks.length === 0 ? (
                      <p className="mt-3 border border-dashed border-ink/20 bg-cream/60 px-3 py-2 text-xs text-ink/55">
                        Sin disponibilidad. Agrega un bloque si puedes acompañar este día.
                      </p>
                    ) : (
                      <div className="mt-3 space-y-2">
                        {blocks.map((block, index) => (
                          <div key={`${day.dia}-${index}`} className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
                            <div className="space-y-1">
                              <Label htmlFor={`inicio-${day.dia}-${index}`}>Desde</Label>
                              <Input
                                id={`inicio-${day.dia}-${index}`}
                                type="time"
                                step={3600}
                                min={day.inicio}
                                max={day.fin}
                                value={block.inicio}
                                onChange={(event) => updateBlock(day.dia, index, "inicio", event.target.value)}
                              />
                            </div>
                            <div className="space-y-1">
                              <Label htmlFor={`fin-${day.dia}-${index}`}>Hasta</Label>
                              <Input
                                id={`fin-${day.dia}-${index}`}
                                type="time"
                                step={3600}
                                min={day.inicio}
                                max={day.fin}
                                value={block.fin}
                                onChange={(event) => updateBlock(day.dia, index, "fin", event.target.value)}
                              />
                            </div>
                            <Button type="button" size="sm" variant="ghost" onClick={() => removeBlock(day.dia, index)}>
                              Quitar
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          <section className="poster-card p-5 sm:p-6">
            <div className="flex items-end justify-between border-b border-ink/15 pb-3">
              <div>
                <p className="type-kicker">Materias</p>
                <h2 className="mt-2 font-display text-2xl uppercase text-primary">¿Qué puedes acompañar?</h2>
              </div>
              <span className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/40">{Object.keys(selected).length} seleccionadas</span>
            </div>

            <div className="mt-4 grid gap-2 sm:grid-cols-[1fr_auto_auto]">
              <input
                value={materiaSearch}
                onChange={(event) => setMateriaSearch(event.target.value)}
                placeholder="Buscar materia..."
                aria-label="Buscar materia"
                className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              />
              <select
                aria-label="Filtrar materias por nivel"
                className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={materiaNivel}
                onChange={(event) => setMateriaNivel(event.target.value)}
              >
                <option value="">Nivel: todos</option>
                <option value="PREPA">Preparatoria</option>
                <option value="LICENCIATURA">Licenciatura</option>
              </select>
              <select
                aria-label="Ordenar materias"
                className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={materiaSort}
                onChange={(event) => setMateriaSort(event.target.value)}
              >
                <option value="nombre-asc">Nombre A-Z</option>
                <option value="nombre-desc">Nombre Z-A</option>
                <option value="nivel-asc">Nivel</option>
                <option value="area-asc">Área</option>
              </select>
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
              <p className="font-mono text-[0.6rem] uppercase tracking-[0.08em] text-ink/45">
                {filteredMaterias.length} visibles
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setSelected((current) => ({
                      ...current,
                      ...Object.fromEntries(
                        filteredMaterias
                          .filter((materia) => !current[materia.id])
                          .map((materia) => [materia.id, { pref: 1, vetada: false }]),
                      ),
                    }))
                  }
                >
                  Seleccionar visibles
                </Button>
                <Button size="sm" variant="outline" onClick={() => setSelected({})}>
                  Limpiar selección
                </Button>
              </div>
            </div>

            {materias && materias.length > 0 ? (
              <div className="mt-4 max-h-[420px] space-y-2 overflow-auto pr-1">
                {filteredMaterias.length === 0 && (
                  <p className="border border-dashed border-ink/20 bg-sand/30 px-3 py-4 text-xs text-ink/55">
                    No hay materias que coincidan con la búsqueda.
                  </p>
                )}
                {filteredMaterias.map((materia) => {
                  const state = selected[materia.id] || { pref: 1, vetada: false };
                  const checked = !!selected[materia.id];
                  return (
                    <div key={materia.id} className={`border p-3 transition ${checked ? "border-primary bg-primary/5" : "border-ink/15"}`}>
                      <label className="flex cursor-pointer items-start gap-3">
                        <input
                          type="checkbox"
                          className="mt-1 h-4 w-4 accent-[#A92730]"
                          checked={checked}
                          onChange={(e) => setSelected(e.target.checked ? { ...selected, [materia.id]: state } : Object.fromEntries(Object.entries(selected).filter(([key]) => Number(key) !== materia.id)))}
                        />
                        <span>
                          <span className="block text-sm font-semibold text-ink">{materia.nombre}</span>
                          <span className="mt-0.5 block font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">{materia.nivel} · {materia.area}</span>
                        </span>
                      </label>
                      {checked && (
                        <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-ink/10 pt-3">
                          <select
                            aria-label={`Preferencia para ${materia.nombre}`}
                            className="h-8 border border-ink/30 bg-surface px-2 text-xs text-ink outline-none focus-visible:border-primary"
                            value={state.pref}
                            onChange={(e) => setSelected({ ...selected, [materia.id]: { ...state, pref: Number(e.target.value) } })}
                          >
                            <option value={1}>Preferencia alta</option>
                            <option value={2}>Preferencia media</option>
                            <option value={3}>Preferencia baja</option>
                          </select>
                          <label className="flex items-center gap-2 text-xs text-ink/60">
                            <input type="checkbox" className="h-4 w-4 accent-[#A92730]" checked={state.vetada} onChange={(e) => setSelected({ ...selected, [materia.id]: { ...state, vetada: e.target.checked } })} />
                            No asignar
                          </label>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="mt-4">
                <EmptyState title="Sin materias" description="Todavía no hay materias en el catálogo para seleccionar." />
              </div>
            )}
          </section>
        </div>

        <div className="flex flex-wrap items-center gap-3 border-t border-ink/15 pt-5">
          <Button onClick={save} disabled={saving || loading}>{saving ? "Guardando..." : "Guardar disponibilidad"}</Button>
          {msg && <p role="status" className="text-sm font-semibold text-accent-deep">{msg}</p>}
        </div>
      </div>
    </AppShell>
  );
}
