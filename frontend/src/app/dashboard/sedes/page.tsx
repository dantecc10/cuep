"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

interface Sede { id: number; nombre: string; ciudad: string | null; }

export default function SedesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [nombre, setNombre] = useState("");
  const [ciudad, setCiudad] = useState("");
  const [codigo, setCodigo] = useState("");

  const { data } = useQuery<Sede[]>({
    queryKey: ["sedes"],
    queryFn: async () => (await api.get("/sedes", { headers })).data,
  });

  const createMutation = useMutation({
    mutationFn: async () => api.post("/sedes", { nombre, ciudad, codigo }, { headers }),
    onSuccess: () => { setNombre(""); setCiudad(""); setCodigo(""); queryClient.invalidateQueries({ queryKey: ["sedes"] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/sedes/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sedes"] }),
  });

  return (
    <AppShell title="Sedes">
      <div className="space-y-4">
        <div className="flex gap-2">
          <Input placeholder="Nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          <Input placeholder="Ciudad" value={ciudad} onChange={(e) => setCiudad(e.target.value)} />
          <Input placeholder="Código (1 carácter)" value={codigo} onChange={(e) => setCodigo(e.target.value)} />
          <Button onClick={() => createMutation.mutate()} disabled={!nombre || !codigo}>Crear</Button>
        </div>
        <div className="space-y-2">
          {(data || []).map((sede) => (
            <div key={sede.id} className="flex items-center justify-between border border-primary bg-surface rounded-card p-3">
              <span>{sede.nombre} {sede.ciudad ? `— ${sede.ciudad}` : ""}</span>
              <Button variant="outline" size="sm" onClick={() => deleteMutation.mutate(sede.id)}>Eliminar</Button>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
