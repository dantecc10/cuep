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
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";

interface Sede { id: number; nombre: string; }
interface Materia { id: number; nombre: string; }
interface Grupo { id: number; nombre: string; materia_id: number; horas_totales: number; capacidad: number; min_alumnos: number; }

export default function GruposPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { confirm, dialog } = useConfirmDialog();
  const [sedeId, setSedeId] = useState(1);
  const [materiaId, setMateriaId] = useState(1);
  const [nombre, setNombre] = useState("");
  const [horas, setHoras] = useState(4);
  const [capacidad, setCapacidad] = useState(30);
  const [minAlumnos, setMinAlumnos] = useState(0);

  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });
  const { data: materias } = useQuery<Materia[]>({ queryKey: ["materias"], queryFn: async () => (await api.get("/materias", { headers })).data });
  const { data: grupos, isLoading } = useQuery<Grupo[]>({ queryKey: ["grupos", sedeId], queryFn: async () => (await api.get(`/sedes/${sedeId}/grupos`, { headers })).data });

  useEffect(() => {
    if (!sedeId && sedes?.length) setSedeId(sedes[0].id);
    if (!materiaId && materias?.length) setMateriaId(materias[0].id);
  }, [sedeId, sedes, materiaId, materias]);

  const createMutation = useMutation({
    mutationFn: async () => api.post(`/sedes/${sedeId}/grupos`, { materia_id: materiaId, nombre, horas_totales: horas, capacidad, min_alumnos: minAlumnos }, { headers }),
    onSuccess: () => { setNombre(""); queryClient.invalidateQueries({ queryKey: ["grupos", sedeId] }); },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/sedes/grupos/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["grupos", sedeId] }),
  });

  const columns: Column<Grupo>[] = [
    {
      key: "nombre",
      header: "Grupo",
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.nombre}</p>
          <p className="text-xs text-ink/50">Materia #{item.materia_id}</p>
        </div>
      ),
    },
    { key: "horas_totales", header: "Horas", render: (item) => `${item.horas_totales} h` },
    { key: "capacidad", header: "Capacidad", render: (item) => `${item.capacidad} lugares` },
    { key: "min_alumnos", header: "Mínimo", render: (item) => `${item.min_alumnos} alumnos` },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <Button
          size="sm"
          variant="outline"
          onClick={async () => {
            if (await confirm({ title: "Eliminar grupo", description: `¿Eliminar el grupo ${item.nombre}?` })) deleteMutation.mutate(item.id);
          }}
        >
          Eliminar
        </Button>
      ),
    },
  ];

  return (
    <AppShell title="Grupos">
      <div className="space-y-6">
        <PageHeader title="Grupos" description="Abre grupos por sede, define capacidad y cupo mínimo para la generación de horarios." />

        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }} className="poster-card space-y-4 p-5 sm:p-6">
          <div>
            <p className="type-kicker">Nuevo grupo</p>
            <h2 className="mt-2 font-display text-3xl uppercase text-primary">Abrir un grupo</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="grupo-sede">Sede</Label>
              <select
                id="grupo-sede"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={sedeId}
                onChange={(e) => setSedeId(Number(e.target.value))}
              >
                {(sedes || []).map((sede) => <option key={sede.id} value={sede.id}>{sede.nombre}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="grupo-materia">Materia</Label>
              <select
                id="grupo-materia"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={materiaId}
                onChange={(e) => setMateriaId(Number(e.target.value))}
              >
                {(materias || []).map((materia) => <option key={materia.id} value={materia.id}>{materia.nombre}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="grupo-nombre">Nombre del grupo</Label>
              <Input id="grupo-nombre" placeholder="Ej. Matutino A" value={nombre} onChange={(e) => setNombre(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="grupo-horas">Horas totales</Label>
              <Input id="grupo-horas" type="number" min={1} value={horas} onChange={(e) => setHoras(Number(e.target.value))} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="grupo-capacidad">Capacidad</Label>
              <Input id="grupo-capacidad" type="number" min={1} value={capacidad} onChange={(e) => setCapacidad(Number(e.target.value))} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="grupo-minimo">Mínimo de alumnos</Label>
              <Input id="grupo-minimo" type="number" min={0} value={minAlumnos} onChange={(e) => setMinAlumnos(Number(e.target.value))} />
            </div>
          </div>
          <Button type="submit" disabled={!nombre || !sedeId || !materiaId}>Crear grupo</Button>
        </form>

        {!isLoading && (!grupos || grupos.length === 0) ? (
          <EmptyState title="Sin grupos" description="Abre el primer grupo de esta sede para comenzar a organizar las asesorías." />
        ) : (
          <DataTable columns={columns} data={grupos} isLoading={isLoading} keyExtractor={(item) => item.id} />
        )}
        {dialog}
      </div>
    </AppShell>
  );
}
