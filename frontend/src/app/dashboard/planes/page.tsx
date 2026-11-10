"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

interface Plan { id: number; nombre: string; nivel: string; area: string | null; descripcion: string | null; }
interface Materia { id: number; nombre: string; nivel: string; area: string; }

export default function PlanesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [nombre, setNombre] = useState("");
  const [nivel, setNivel] = useState("PREPA");
  const [area, setArea] = useState("");
  const [selectedPlan, setSelectedPlan] = useState<number | null>(null);
  const [selectedMaterias, setSelectedMaterias] = useState<number[]>([]);

  const { data: planes } = useQuery<Plan[]>({ queryKey: ["planes"], queryFn: async () => (await api.get("/planes", { headers })).data });
  const { data: materias } = useQuery<Materia[]>({ queryKey: ["materias"], queryFn: async () => (await api.get("/materias", { headers })).data });
  const { data: planMaterias } = useQuery<Materia[]>({
    queryKey: ["plan-materias", selectedPlan],
    queryFn: async () => (await api.get(`/planes/${selectedPlan}/materias`, { headers })).data,
    enabled: !!selectedPlan,
  });

  const createMutation = useMutation({
    mutationFn: async () => api.post("/planes", { nombre, nivel, area: area || null }, { headers }),
    onSuccess: () => { setNombre(""); setArea(""); queryClient.invalidateQueries({ queryKey: ["planes"] }); },
  });

  const setMateriasMutation = useMutation({
    mutationFn: async () => api.put(`/planes/${selectedPlan}/materias`, { materia_ids: selectedMaterias }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["plan-materias", selectedPlan] }),
  });

  return (
    <AppShell title="Planes de estudio">
      <div className="space-y-6">
        <div className="flex gap-2">
          <Input placeholder="Nombre del plan" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          <select className="border border-primary rounded-button p-2 bg-surface" value={nivel} onChange={(e) => setNivel(e.target.value)}>
            <option value="PREPA">Prepa</option>
            <option value="LICENCIATURA">Licenciatura</option>
          </select>
          <Input placeholder="Área" value={area} onChange={(e) => setArea(e.target.value)} />
          <Button onClick={() => createMutation.mutate()} disabled={!nombre}>Crear plan</Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <h2 className="font-display text-2xl uppercase text-primary">Planes</h2>
            {(planes || []).map((plan) => (
              <button key={plan.id} onClick={() => { setSelectedPlan(plan.id); setSelectedMaterias([]); }} className="w-full text-left border border-primary bg-surface rounded-card p-3 hover:bg-paper">
                {plan.nombre} — {plan.nivel} {plan.area ? `(${plan.area})` : ""}
              </button>
            ))}
          </div>
          <div className="space-y-2">
            <h2 className="font-display text-2xl uppercase text-primary">Materias del plan</h2>
            {selectedPlan && (
              <>
                <div className="max-h-64 overflow-auto space-y-1">
                  {(materias || []).map((m) => (
                    <label key={m.id} className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={selectedMaterias.includes(m.id)} onChange={(e) => setSelectedMaterias(e.target.checked ? [...selectedMaterias, m.id] : selectedMaterias.filter((x) => x !== m.id))} />
                      {m.nombre} ({m.nivel})
                    </label>
                  ))}
                </div>
                <Button onClick={() => setMateriasMutation.mutate()}>Guardar materias</Button>
                <div className="text-sm">
                  {(planMaterias || []).map((m) => <span key={m.id} className="mr-2">{m.nombre}</span>)}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
