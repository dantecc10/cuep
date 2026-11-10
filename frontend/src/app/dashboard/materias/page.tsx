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

interface Materia { id: number; nombre: string; nivel: string; area: string; descripcion: string | null; }

const initialForm = { nombre: "", nivel: "PREPA", area: "Exactas", descripcion: "" };

export default function MateriasPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { confirm, dialog } = useConfirmDialog();
  const [form, setForm] = useState(initialForm);

  const { data, isLoading } = useQuery<Materia[]>({
    queryKey: ["materias"],
    queryFn: async () => (await api.get("/materias", { headers })).data,
  });

  const createMutation = useMutation({
    mutationFn: async () => api.post("/materias", { ...form, descripcion: form.descripcion || null }, { headers }),
    onSuccess: () => { setForm(initialForm); queryClient.invalidateQueries({ queryKey: ["materias"] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/materias/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["materias"] }),
  });

  const columns: Column<Materia>[] = [
    {
      key: "nombre",
      header: "Materia",
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.nombre}</p>
          {item.descripcion && <p className="mt-0.5 max-w-md text-xs text-ink/55">{item.descripcion}</p>}
        </div>
      ),
    },
    { key: "nivel", header: "Nivel", render: (item) => (item.nivel === "PREPA" ? "Preparatoria" : "Licenciatura") },
    { key: "area", header: "Área" },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <Button
          size="sm"
          variant="outline"
          onClick={async () => {
            if (await confirm({ title: "Eliminar materia", description: `¿Eliminar ${item.nombre} del catálogo?` })) {
              deleteMutation.mutate(item.id);
            }
          }}
        >
          Eliminar
        </Button>
      ),
    },
  ];

  return (
    <AppShell title="Materias">
      <div className="space-y-6">
        <PageHeader title="Materias" description="Catálogo académico que alimenta los planes de estudio y las asesorías." />

        <form
          onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }}
          className="poster-card space-y-4 p-5 sm:p-6"
        >
          <div>
            <p className="type-kicker">Nueva materia</p>
            <h2 className="mt-2 font-display text-3xl uppercase text-primary">Agregar al catálogo</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2 lg:col-span-2">
              <Label htmlFor="materia-nombre">Nombre</Label>
              <Input id="materia-nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="materia-nivel">Nivel</Label>
              <select
                id="materia-nivel"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={form.nivel}
                onChange={(e) => setForm({ ...form, nivel: e.target.value })}
              >
                <option value="PREPA">Preparatoria</option>
                <option value="LICENCIATURA">Licenciatura</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="materia-area">Área</Label>
              <Input id="materia-area" value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} required />
            </div>
            <div className="space-y-2 md:col-span-2 lg:col-span-3">
              <Label htmlFor="materia-descripcion">Descripción</Label>
              <Input id="materia-descripcion" value={form.descripcion} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
            </div>
            <div className="flex items-end">
              <Button type="submit" className="h-10 w-full" disabled={!form.nombre || !form.area}>Agregar materia</Button>
            </div>
          </div>
        </form>

        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin materias" description="Agrega la primera materia del catálogo para comenzar a armar planes y grupos." />
        ) : (
          <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />
        )}
        {dialog}
      </div>
    </AppShell>
  );
}
