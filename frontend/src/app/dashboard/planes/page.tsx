"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/ui/empty-state";

interface Plan { id: number; nombre: string; nivel: string; area: string | null; descripcion: string | null; }
interface Materia { id: number; nombre: string; nivel: string; area: string; }

export default function PlanesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ nombre: "", nivel: "PREPA", area: "" });
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null);
  const [selectedMaterias, setSelectedMaterias] = useState<number[]>([]);

  const { data: planes, isLoading: loadingPlanes } = useQuery<Plan[]>({ queryKey: ["planes"], queryFn: async () => (await api.get("/planes", { headers })).data });
  const { data: materias } = useQuery<Materia[]>({ queryKey: ["materias"], queryFn: async () => (await api.get("/materias", { headers })).data });
  const { data: planMaterias } = useQuery<Materia[]>({
    queryKey: ["plan-materias", selectedPlan],
    queryFn: async () => (await api.get(`/planes/${selectedPlan}/materias`, { headers })).data,
    enabled: !!selectedPlan,
  });

  const createMutation = useMutation({
    mutationFn: async () => api.post("/planes", { nombre: form.nombre, nivel: form.nivel, area: form.area || null }, { headers }),
    onSuccess: () => { setForm({ nombre: "", nivel: "PREPA", area: "" }); queryClient.invalidateQueries({ queryKey: ["planes"] }); },
  });

  const setMateriasMutation = useMutation({
    mutationFn: async () => api.put(`/planes/${selectedPlan}/materias`, { materia_ids: selectedMaterias }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plan-materias", selectedPlan] }),
  });

  const planActivo = (planes || []).find((plan) => plan.id === selectedPlan);

  useEffect(() => {
    if (selectedPlan) setSelectedMaterias((planMaterias || []).map((materia) => materia.id));
  }, [planMaterias, selectedPlan]);

  function toggleMateria(id: number) {
    setSelectedMaterias((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  return (
    <AppShell title="Planes de estudio">
      <div className="space-y-6">
        <PageHeader title="Planes de estudio" description="Organiza las materias que forman cada plan del colectivo." />

        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }} className="poster-card space-y-4 p-5 sm:p-6">
          <div>
            <p className="type-kicker">Nuevo plan</p>
            <h2 className="mt-2 font-display text-3xl uppercase text-primary">Crear plan de estudios</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-[1.4fr_0.8fr_0.8fr_auto] md:items-end">
            <div className="space-y-2">
              <Label htmlFor="plan-nombre">Nombre</Label>
              <Input id="plan-nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="plan-nivel">Nivel</Label>
              <select
                id="plan-nivel"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={form.nivel}
                onChange={(e) => setForm({ ...form, nivel: e.target.value })}
              >
                <option value="PREPA">Preparatoria</option>
                <option value="LICENCIATURA">Licenciatura</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="plan-area">Área</Label>
              <Input id="plan-area" value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} />
            </div>
            <Button type="submit" className="h-10" disabled={!form.nombre}>Crear plan</Button>
          </div>
        </form>

        <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="space-y-3">
            <div className="flex items-end justify-between border-b border-ink/15 pb-3">
              <h2 className="font-display text-2xl uppercase text-primary">Planes existentes</h2>
              <span className="font-mono text-[0.62rem] uppercase tracking-[0.1em] text-ink/40">{planes?.length || 0} registros</span>
            </div>
            {!loadingPlanes && (!planes || planes.length === 0) ? (
              <EmptyState title="Sin planes" description="Crea el primer plan de estudios para asignarle materias." />
            ) : (
              <div className="space-y-2">
                {(planes || []).map((plan) => (
                  <button
                    key={plan.id}
                    type="button"
                    onClick={() => setSelectedPlan(plan.id)}
                    className={`w-full border p-4 text-left transition ${
                      selectedPlan === plan.id
                        ? "border-ink bg-yellow shadow-[3px_3px_0_#171313]"
                        : "border-ink/20 bg-surface hover:border-ink hover:bg-sand"
                    }`}
                  >
                    <p className="type-label text-ink/45">{plan.nivel === "PREPA" ? "Preparatoria" : "Licenciatura"}{plan.area ? ` · ${plan.area}` : ""}</p>
                    <p className="mt-1 font-display text-xl uppercase text-ink">{plan.nombre}</p>
                  </button>
                ))}
              </div>
            )}
          </section>

          <section className="poster-card p-5 sm:p-6">
            <div className="border-b border-ink/15 pb-3">
              <p className="type-label text-ink/40">Materias del plan</p>
              <h2 className="mt-1 font-display text-2xl uppercase text-primary">{planActivo?.nombre || "Selecciona un plan"}</h2>
            </div>

            {selectedPlan ? (
              <div className="mt-4 space-y-4">
                <div className="max-h-80 space-y-1 overflow-auto pr-1">
                  {(materias || []).map((materia) => {
                    const checked = selectedMaterias.includes(materia.id);
                    return (
                      <label key={materia.id} className={`flex cursor-pointer items-start gap-3 border p-3 transition ${checked ? "border-primary bg-primary/5" : "border-ink/15 hover:bg-sand"}`}>
                        <input
                          type="checkbox"
                          className="mt-1 h-4 w-4 accent-[#A92730]"
                          checked={checked}
                          onChange={() => toggleMateria(materia.id)}
                        />
                        <span>
                          <span className="block text-sm font-semibold text-ink">{materia.nombre}</span>
                          <span className="mt-0.5 block font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">{materia.nivel} · {materia.area}</span>
                        </span>
                      </label>
                    );
                  })}
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink/10 pt-4">
                  <p className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/45">{selectedMaterias.length} seleccionadas</p>
                  <Button onClick={() => setMateriasMutation.mutate()} disabled={setMateriasMutation.isPending}>Guardar materias</Button>
                </div>
                {(planMaterias || []).length > 0 && (
                  <p className="text-xs leading-relaxed text-ink/50">
                    Actualmente asignadas: {(planMaterias || []).map((materia) => materia.nombre).join(", ")}
                  </p>
                )}
              </div>
            ) : (
              <p className="mt-4 font-editorial text-base text-ink/55">Elige un plan de la lista para revisar y asignar sus materias.</p>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}
