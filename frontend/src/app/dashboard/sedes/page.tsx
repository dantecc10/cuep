"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell } from "@/components/layout/app-shell";

interface Sede { id: number; nombre: string; ciudad: string | null; codigo: string | null; descripcion: string | null; maps_url: string | null; image_url: string | null; activo: boolean; }

const empty = { nombre: "", ciudad: "", codigo: "", descripcion: "", maps_url: "", image_url: "", activo: true };

export default function SedesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState<number | null>(null);

  const { data } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });

  const saveMutation = useMutation({
    mutationFn: async () => editingId ? api.put(`/sedes/${editingId}`, form, { headers }) : api.post("/sedes", form, { headers }),
    onSuccess: () => { setForm(empty); setEditingId(null); queryClient.invalidateQueries({ queryKey: ["sedes"] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/sedes/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sedes"] }),
  });

  return (
    <AppShell title="Sedes">
      <div className="space-y-6">
        <form onSubmit={(e) => { e.preventDefault(); saveMutation.mutate(); }} className="bg-surface border border-primary rounded-card p-6 space-y-4">
          <h2 className="font-display text-2xl uppercase text-primary">{editingId ? "Editar sede" : "Nueva sede"}</h2>
          <div className="grid gap-3 md:grid-cols-2">
            <div><Label>Nombre</Label><Input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required /></div>
            <div><Label>Ciudad</Label><Input value={form.ciudad} onChange={(e) => setForm({ ...form, ciudad: e.target.value })} /></div>
            <div><Label>Código</Label><Input value={form.codigo} onChange={(e) => setForm({ ...form, codigo: e.target.value })} required maxLength={1} /></div>
            <div><Label>Imagen (URL)</Label><Input value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} /></div>
            <div className="md:col-span-2"><Label>Descripción</Label><Input value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} /></div>
            <div className="md:col-span-2"><Label>Google Maps (URL)</Label><Input value={form.maps_url} onChange={(e) => setForm({ ...form, maps_url: e.target.value })} /></div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={!form.nombre || !form.codigo}>{editingId ? "Guardar cambios" : "Crear sede"}</Button>
            {editingId && <Button type="button" variant="outline" onClick={() => { setEditingId(null); setForm(empty); }}>Cancelar</Button>}
          </div>
        </form>
        <div className="space-y-2">
          {(data || []).map((sede) => (
            <div key={sede.id} className="border border-primary bg-surface rounded-card p-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="font-semibold">{sede.nombre} {sede.codigo ? `(${sede.codigo})` : ""}</p>
                <p className="text-sm">{sede.ciudad || "Sin ciudad"} {sede.descripcion ? `— ${sede.descripcion}` : ""}</p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => { setEditingId(sede.id); setForm({ nombre: sede.nombre, ciudad: sede.ciudad || "", codigo: sede.codigo || "", descripcion: sede.descripcion || "", maps_url: sede.maps_url || "", image_url: sede.image_url || "", activo: sede.activo }); }}>Editar</Button>
                <Button size="sm" variant="outline" onClick={() => deleteMutation.mutate(sede.id)}>Eliminar</Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
