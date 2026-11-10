"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/ui/empty-state";

interface Materia { id: number; nombre: string; nivel: string; area: string; }

const diasSemana = [
  { value: 1, label: "Lun" },
  { value: 2, label: "Mar" },
  { value: 3, label: "Mié" },
  { value: 4, label: "Jue" },
  { value: 5, label: "Vie" },
  { value: 6, label: "Sáb" },
];

export default function DisponibilidadPage() {
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const { data: materias } = useQuery<Materia[]>({ queryKey: ["materias"], queryFn: async () => (await api.get("/materias", { headers })).data });

  const [days, setDays] = useState<number[]>([1]);
  const [start, setStart] = useState("08:00");
  const [end, setEnd] = useState("14:00");
  const [selected, setSelected] = useState<Record<number, { pref: number; vetada: boolean }>>({});
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  async function save() {
    if (!user) return;
    setSaving(true);
    setMsg("");
    const disponibilidad = days.map((d) => ({ dia_semana: d, hora_inicio: start, hora_fin: end }));
    const materiasPayload = Object.entries(selected).map(([id, v]) => ({ materia_id: Number(id), nivel_preferencia: v.pref, vetada: v.vetada }));
    try {
      await api.put(`/tutores/${user.id}/disponibilidad`, { disponibilidad, materias: materiasPayload }, { headers });
      setMsg("Disponibilidad guardada correctamente.");
    } catch {
      setMsg("No pudimos guardar tu disponibilidad. Inténtalo de nuevo.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell title="Disponibilidad">
      <div className="space-y-6">
        <PageHeader title="Disponibilidad y materias" description="Marca cuándo puedes dar asesoría y qué materias quieres acompañar." />

        <div className="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <section className="poster-card h-fit p-5 sm:p-6">
            <p className="type-kicker">Horario base</p>
            <h2 className="mt-2 font-display text-2xl uppercase text-primary">Días y horas</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {diasSemana.map((dia) => {
                const active = days.includes(dia.value);
                return (
                  <button
                    key={dia.value}
                    type="button"
                    onClick={() => setDays(active ? days.filter((d) => d !== dia.value) : [...days, dia.value])}
                    className={`border px-3 py-2 font-mono text-[0.62rem] font-bold uppercase tracking-[0.08em] transition ${
                      active ? "border-ink bg-yellow text-ink shadow-[2px_2px_0_#171313]" : "border-ink/20 text-ink/55 hover:border-ink"
                    }`}
                  >
                    {dia.label}
                  </button>
                );
              })}
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="hora-inicio">Desde</Label>
                <Input id="hora-inicio" type="time" value={start} onChange={(e) => setStart(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hora-fin">Hasta</Label>
                <Input id="hora-fin" type="time" value={end} onChange={(e) => setEnd(e.target.value)} />
              </div>
            </div>
            <p className="mt-4 border-l-2 border-yellow bg-yellow/10 px-3 py-2 text-xs leading-relaxed text-ink/60">
              La coordinación usará este rango para asignarte grupos. Puedes ajustarlo cuando cambie tu disponibilidad.
            </p>
          </section>

          <section className="poster-card p-5 sm:p-6">
            <div className="flex items-end justify-between border-b border-ink/15 pb-3">
              <div>
                <p className="type-kicker">Materias</p>
                <h2 className="mt-2 font-display text-2xl uppercase text-primary">¿Qué puedes acompañar?</h2>
              </div>
              <span className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/40">{Object.keys(selected).length} seleccionadas</span>
            </div>

            {materias && materias.length > 0 ? (
              <div className="mt-4 max-h-[420px] space-y-2 overflow-auto pr-1">
                {materias.map((materia) => {
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
          <Button onClick={save} disabled={saving}>{saving ? "Guardando..." : "Guardar disponibilidad"}</Button>
          {msg && <p role="status" className="text-sm font-semibold text-accent-deep">{msg}</p>}
        </div>
      </div>
    </AppShell>
  );
}
