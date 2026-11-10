"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

interface Materia { id: number; nombre: string; nivel: string; area: string; descripcion: string | null; }

export default function MateriasPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [nombre, setNombre] = useState("");
  const [nivel, setNivel] = useState("PREPA");
  const [area, setArea] = useState("Exactas");
  const [descripcion, setDescripcion] = useState("");

  const { data } = useQuery<Materia[]>({
    queryKey: ["materias"],
    queryFn: async () => (await api.get("/materias", { headers })).data,
  });

  const createMutation = useMutation({
    mutationFn: async () => api.post("/materias", { nombre, nivel, area, descripcion }, { headers }),
    onSuccess: () => { setNombre(""); setDescripcion(""); queryClient.invalidateQueries({ queryKey: ["materias"] }); },
  });
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/materias/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["materias"] }),
  });

  return (
    <AppShell title="Materias">
      <div className="space-y-4">
        <div className="flex gap-2">
          <Input placeholder="Nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          <select className="border border-primary rounded-button p-2 bg-surface" value={nivel} onChange={(e) => setNivel(e.target.value)}>
            <option value="PREPA">Prepa</option>
            <option value="LICENCIATURA">Licenciatura</option>
          </select>
          <Input placeholder="Área" value={area} onChange={(e) => setArea(e.target.value)} />
          <Input placeholder="Descripción" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
          <Button onClick={() => createMutation.mutate()} disabled={!nombre}>Crear</Button>
        </div>
        <div className="space-y-2">
          {(data || []).map((m) => (
            <div key={m.id} className="border border-primary bg-surface rounded-card p-3">
              <p className="font-semibold">{m.nombre}</p>
              <p className="text-sm">{m.nivel} — {m.area}</p>
              {m.descripcion && <p className="text-sm text-muted-foreground">{m.descripcion}</p>}
              <Button size="sm" variant="outline" onClick={() => deleteMutation.mutate(m.id)}>Eliminar</Button>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
