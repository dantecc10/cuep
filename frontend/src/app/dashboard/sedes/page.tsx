"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";

interface Sede { id: number; nombre: string; ciudad: string | null; codigo: string | null; descripcion: string | null; maps_url: string | null; image_url: string | null; activo: boolean; }

const empty = { nombre: "", ciudad: "", codigo: "", descripcion: "", maps_url: "", image_url: "", activo: true };

export default function SedesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { confirm, dialog } = useConfirmDialog();
  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState<number | null>(null);

  const { data, isLoading } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });

  const saveMutation = useMutation({
    mutationFn: async () => editingId ? api.put(`/sedes/${editingId}`, form, { headers }) : api.post("/sedes", form, { headers }),
    onSuccess: () => { setForm(empty); setEditingId(null); queryClient.invalidateQueries({ queryKey: ["sedes"] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/sedes/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sedes"] }),
  });

  const columns: Column<Sede>[] = [
    { key: "nombre", header: "Nombre" },
    { key: "codigo", header: "Código" },
    { key: "ciudad", header: "Ciudad" },
    { key: "activo", header: "Activo", render: (item) => (item.activo ? "Sí" : "No") },
    {
      key: "acciones",
      header: "Acciones",
      render: (item) => (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => { setEditingId(item.id); setForm({ nombre: item.nombre, ciudad: item.ciudad || "", codigo: item.codigo || "", descripcion: item.descripcion || "", maps_url: item.maps_url || "", image_url: item.image_url || "", activo: item.activo }); }}>Editar</Button>
          <Button size="sm" variant="outline" onClick={async () => { if (await confirm({ title: "Eliminar sede", description: "¿Eliminar esta sede?" })) deleteMutation.mutate(item.id); }}>Eliminar</Button>
        </div>
      ),
    },
  ];

  return (
    <AppShell title="">
      <div className="space-y-6">
        <PageHeader title="Sedes" description="Gestión de sedes del colectivo." actions={<Button onClick={() => { setEditingId(null); setForm(empty); }}>Nueva sede</Button>} />
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
        {!isLoading && (!data || data.length === 0) ? <EmptyState title="Sin sedes" description="Crea la primera sede del colectivo." /> : <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />}
        {dialog}
      </div>
    </AppShell>
  );
}
