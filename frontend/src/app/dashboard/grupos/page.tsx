"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

interface Sede { id: number; nombre: string; }
interface Materia { id: number; nombre: string; }
interface Grupo { id: number; nombre: string; materia_id: number; horas_totales: number; capacidad: number; min_alumnos: number; }

export default function GruposPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [sedeId, setSedeId] = useState(1);
  const [materiaId, setMateriaId] = useState(1);
  const [nombre, setNombre] = useState("");
  const [horas, setHoras] = useState(4);
  const [capacidad, setCapacidad] = useState(30);

  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });
  const { data: materias } = useQuery<Materia[]>({ queryKey: ["materias"], queryFn: async () => (await api.get("/materias", { headers })).data });
  const { data: grupos } = useQuery<Grupo[]>({ queryKey: ["grupos", sedeId], queryFn: async () => (await api.get(`/sedes/${sedeId}/grupos`, { headers })).data });

  const createMutation = useMutation({
    mutationFn: async () => api.post(`/sedes/${sedeId}/grupos`, { materia_id: materiaId, nombre, horas_totales: horas, capacidad }, { headers }),
    onSuccess: () => { setNombre(""); queryClient.invalidateQueries({ queryKey: ["grupos", sedeId] }); },
  });

  return (
    <AppShell title="Grupos">
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <select className="border border-primary rounded-button p-2 bg-surface" value={sedeId} onChange={(e) => setSedeId(Number(e.target.value))}>
            {(sedes || []).map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
          </select>
          <select className="border border-primary rounded-button p-2 bg-surface" value={materiaId} onChange={(e) => setMateriaId(Number(e.target.value))}>
            {(materias || []).map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
          </select>
          <Input placeholder="Nombre del grupo" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          <Input type="number" placeholder="Horas" value={horas} onChange={(e) => setHoras(Number(e.target.value))} />
          <Input type="number" placeholder="Capacidad" value={capacidad} onChange={(e) => setCapacidad(Number(e.target.value))} />
          <Button onClick={() => createMutation.mutate()} disabled={!nombre}>Crear grupo</Button>
        </div>
        <div className="space-y-2">
          {(grupos || []).map((g) => (
            <div key={g.id} className="border border-primary bg-surface rounded-card p-3">
              <p className="font-semibold">{g.nombre}</p>
              <p className="text-sm">Materia ID: {g.materia_id} — Horas: {g.horas_totales} — Capacidad: {g.capacidad}</p>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
