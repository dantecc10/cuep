"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/ui/empty-state";
import { PlanFormDialog, type PlanFormValue } from "@/components/shared/plan-form-dialog";
import { MateriaFormDialog } from "@/components/shared/materia-form-dialog";
import { ImportDialog } from "@/components/shared/import-dialog";

interface Plan {
  id: number;
  nombre: string;
  nivel: string;
  area: string | null;
  descripcion: string | null;
  activo: boolean;
}
interface Materia {
  id: number;
  nombre: string;
  nivel: string;
  area: string;
  descripcion?: string | null;
}

function toFormValue(plan: Plan): PlanFormValue {
  return {
    id: plan.id,
    nombre: plan.nombre,
    nivel: plan.nivel,
    area: plan.area || "",
    descripcion: plan.descripcion || "",
    activo: plan.activo,
  };
}

export default function PlanesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null);
  const [selectedMaterias, setSelectedMaterias] = useState<number[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<PlanFormValue | null>(null);
  const [materiaFormOpen, setMateriaFormOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [planSearch, setPlanSearch] = useState("");
  const [planNivel, setPlanNivel] = useState("");
  const [planArea, setPlanArea] = useState("");
  const [planSort, setPlanSort] = useState("nombre-asc");
  const [materiaSearch, setMateriaSearch] = useState("");
  const [materiaNivel, setMateriaNivel] = useState("");
  const [materiaArea, setMateriaArea] = useState("");
  const [materiaSort, setMateriaSort] = useState("nombre-asc");

  const { data: planes, isLoading: loadingPlanes } = useQuery<Plan[]>({
    queryKey: ["planes"],
    queryFn: async () => (await api.get("/planes", { headers })).data,
  });
  const { data: materias } = useQuery<Materia[]>({
    queryKey: ["materias"],
    queryFn: async () => (await api.get("/materias", { headers })).data,
  });
  const { data: planMaterias } = useQuery<Materia[]>({
    queryKey: ["plan-materias", selectedPlan],
    queryFn: async () => (await api.get(`/planes/${selectedPlan}/materias`, { headers })).data,
    enabled: !!selectedPlan,
  });

  const setMateriasMutation = useMutation({
    mutationFn: async () => api.put(`/planes/${selectedPlan}/materias`, { materia_ids: selectedMaterias }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plan-materias", selectedPlan] }),
  });

  const planActivo = (planes || []).find((plan) => plan.id === selectedPlan);

  const planAreaOptions = Array.from(new Set((planes || []).map((plan) => plan.area).filter(Boolean) as string[]))
    .sort((a, b) => a.localeCompare(b, "es"))
    .map((area) => ({ value: area, label: area }));
  const materiaAreaOptions = Array.from(new Set((materias || []).map((materia) => materia.area)))
    .sort((a, b) => a.localeCompare(b, "es"))
    .map((area) => ({ value: area, label: area }));

  const filteredPlans = useMemo(() => {
    let list = [...(planes || [])];
    const term = planSearch.trim().toLocaleLowerCase("es");
    if (term) {
      list = list.filter((plan) =>
        [plan.nombre, plan.nivel, plan.area || "", plan.descripcion || ""]
          .join(" ")
          .toLocaleLowerCase("es")
          .includes(term),
      );
    }
    if (planNivel) list = list.filter((plan) => plan.nivel === planNivel);
    if (planArea) list = list.filter((plan) => plan.area === planArea);
    const [key, direction] = planSort.split("-");
    list.sort((a, b) => {
      const valueA = key === "area" ? a.area || "" : a.nombre;
      const valueB = key === "area" ? b.area || "" : b.nombre;
      return valueA.localeCompare(valueB, "es") * (direction === "desc" ? -1 : 1);
    });
    return list;
  }, [planes, planSearch, planNivel, planArea, planSort]);

  const filteredMaterias = useMemo(() => {
    let list = [...(materias || [])];
    const term = materiaSearch.trim().toLocaleLowerCase("es");
    if (term) {
      list = list.filter((materia) =>
        [materia.nombre, materia.area, materia.nivel, materia.descripcion || ""]
          .join(" ")
          .toLocaleLowerCase("es")
          .includes(term),
      );
    }
    if (materiaNivel) list = list.filter((materia) => materia.nivel === materiaNivel);
    if (materiaArea) list = list.filter((materia) => materia.area === materiaArea);
    const [key, direction] = materiaSort.split("-");
    list.sort((a, b) => {
      const valueA = key === "area" ? a.area : key === "nivel" ? a.nivel : a.nombre;
      const valueB = key === "area" ? b.area : key === "nivel" ? b.nivel : b.nombre;
      return valueA.localeCompare(valueB, "es") * (direction === "desc" ? -1 : 1);
    });
    return list;
  }, [materias, materiaSearch, materiaNivel, materiaArea, materiaSort]);

  useEffect(() => {
    if (selectedPlan) setSelectedMaterias((planMaterias || []).map((materia) => materia.id));
  }, [planMaterias, selectedPlan]);

  function toggleMateria(id: number) {
    setSelectedMaterias((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }

  function selectVisibleMaterias() {
    setSelectedMaterias((current) => Array.from(new Set([...current, ...filteredMaterias.map((materia) => materia.id)])));
  }

  return (
    <AppShell title="Planes de estudio">
      <div className="space-y-6">
        <PageHeader
          title="Planes de estudio"
          description="Organiza las materias que forman cada plan del colectivo."
          actions={
            <>
              <Button
                onClick={() => {
                  setEditingPlan(null);
                  setFormOpen(true);
                }}
              >
                Nuevo plan
              </Button>
              <Button variant="outline" onClick={() => setImportOpen(true)}>
                Importar CSV
              </Button>
            </>
          }
        />

        <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <section className="space-y-3">
            <div className="flex items-end justify-between border-b border-ink/15 pb-3">
              <h2 className="font-display text-2xl uppercase text-primary">Planes existentes</h2>
              <span className="font-mono text-[0.62rem] uppercase tracking-[0.1em] text-ink/40">{filteredPlans.length} de {planes?.length || 0}</span>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                value={planSearch}
                onChange={(event) => setPlanSearch(event.target.value)}
                placeholder="Buscar plan..."
                aria-label="Buscar plan"
                className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              />
              <select
                aria-label="Filtrar planes por nivel"
                className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={planNivel}
                onChange={(event) => setPlanNivel(event.target.value)}
              >
                <option value="">Nivel: todos</option>
                <option value="PREPA">Preparatoria</option>
                <option value="LICENCIATURA">Licenciatura</option>
              </select>
              <select
                aria-label="Filtrar planes por área"
                className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={planArea}
                onChange={(event) => setPlanArea(event.target.value)}
              >
                <option value="">Área: todas</option>
                {planAreaOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <select
                aria-label="Ordenar planes"
                className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={planSort}
                onChange={(event) => setPlanSort(event.target.value)}
              >
                <option value="nombre-asc">Nombre A-Z</option>
                <option value="nombre-desc">Nombre Z-A</option>
                <option value="area-asc">Área A-Z</option>
                <option value="area-desc">Área Z-A</option>
              </select>
            </div>
            {!loadingPlanes && (!planes || planes.length === 0) ? (
              <EmptyState title="Sin planes" description="Crea el primer plan de estudios para asignarle materias." />
            ) : filteredPlans.length === 0 ? (
              <p className="border border-dashed border-ink/20 bg-sand/30 px-3 py-4 text-xs text-ink/55">
                No hay planes que coincidan con la búsqueda.
              </p>
            ) : (
              <div className="space-y-2">
                {filteredPlans.map((plan) => (
                  <div
                    key={plan.id}
                    className={`border p-4 transition ${
                      selectedPlan === plan.id
                        ? "border-ink bg-yellow shadow-[3px_3px_0_#171313]"
                        : "border-ink/20 bg-surface hover:border-ink hover:bg-sand"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <button
                        type="button"
                        onClick={() => setSelectedPlan(plan.id)}
                        className="flex-1 text-left"
                      >
                        <p className="type-label text-ink/45">{plan.nivel === "PREPA" ? "Preparatoria" : "Licenciatura"}{plan.area ? ` · ${plan.area}` : ""}</p>
                        <p className="mt-1 font-display text-xl uppercase text-ink">{plan.nombre}</p>
                      </button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setEditingPlan(toFormValue(plan));
                          setFormOpen(true);
                        }}
                      >
                        Editar
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="poster-card p-5 sm:p-6">
            <div className="border-b border-ink/15 pb-3">
              <p className="type-label text-ink/40">Materias del plan</p>
              <h2 className="mt-1 font-display text-2xl uppercase text-primary">{planActivo?.nombre || "Selecciona un plan"}</h2>
              <p className="mt-1 text-xs text-ink/50">
                Una materia puede pertenecer a varios planes; asignarla aquí no la quita de otros.
              </p>
            </div>

            {selectedPlan ? (
              <div className="mt-4 space-y-4">
                <div className="grid gap-2 sm:grid-cols-2">
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
                    aria-label="Filtrar materias por área"
                    className="h-9 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                    value={materiaArea}
                    onChange={(event) => setMateriaArea(event.target.value)}
                  >
                    <option value="">Área: todas</option>
                    {materiaAreaOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
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
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-mono text-[0.6rem] uppercase tracking-[0.08em] text-ink/45">
                    {filteredMaterias.length} visibles
                  </p>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={selectVisibleMaterias}>
                      Seleccionar visibles
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setSelectedMaterias([])}>
                      Limpiar selección
                    </Button>
                  </div>
                </div>
                <div className="max-h-80 space-y-1 overflow-auto pr-1">
                  {filteredMaterias.length === 0 ? (
                    <p className="border border-dashed border-ink/20 bg-sand/30 px-3 py-4 text-xs text-ink/55">
                      No hay materias que coincidan con la búsqueda.
                    </p>
                  ) : filteredMaterias.map((materia) => {
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
                <div className="flex flex-wrap items-center justify-between gap-3 border border-dashed border-ink/25 bg-sand/40 p-3">
                  <p className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/50">
                    ¿No está la materia?
                  </p>
                  <Button size="sm" variant="outline" onClick={() => setMateriaFormOpen(true)}>
                    Crear nueva materia
                  </Button>
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

        <PlanFormDialog
          open={formOpen}
          onOpenChange={setFormOpen}
          plan={editingPlan}
          onSaved={() => setEditingPlan(null)}
        />
        <MateriaFormDialog
          open={materiaFormOpen}
          onOpenChange={setMateriaFormOpen}
          materia={null}
          onSaved={() => queryClient.invalidateQueries({ queryKey: ["materias"] })}
        />
        <ImportDialog
          entidad="planes"
          open={importOpen}
          onOpenChange={setImportOpen}
          onImported={() => {
            queryClient.invalidateQueries({ queryKey: ["planes"] });
            queryClient.invalidateQueries({ queryKey: ["materias"] });
          }}
        />
      </div>
    </AppShell>
  );
}
