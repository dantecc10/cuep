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
import { StatusBadge } from "@/components/shared/status-badge";
import { SearchableSelect } from "@/components/shared/searchable-select";

interface Sede { id: number; nombre: string; }
interface Corrida { id: number; sede_id: number | null; estado: string; aprobada: boolean; publicada: boolean; progreso: number; etapa: string | null; }

export default function CorridasPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [sedeId, setSedeId] = useState(0);
  const [grupoIds, setGrupoIds] = useState("1");

  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });
  const { data, isLoading } = useQuery<Corrida[]>({ queryKey: ["corridas"], queryFn: async () => (await api.get("/corridas", { headers })).data, refetchInterval: 3000 });
  const createMutation = useMutation({
    mutationFn: async () => api.post("/corridas", { sede_id: sedeId, grupo_ids: grupoIds.split(",").map((x) => Number(x.trim())).filter(Boolean) }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }),
  });

  useEffect(() => {
    if (!sedeId && sedes?.length) setSedeId(sedes[0].id);
  }, [sedeId, sedes]);

  const columns: Column<Corrida>[] = [
    {
      key: "id",
      header: "Corrida",
      sortValue: (item) => item.id,
      render: (item) => <span className="font-mono text-xs font-bold">#{item.id}</span>,
    },
    {
      key: "sede_id",
      header: "Sede",
      sortValue: (item) => sedes?.find((sede) => sede.id === item.sede_id)?.nombre || "",
      render: (item) => sedes?.find((sede) => sede.id === item.sede_id)?.nombre || `Sede ${item.sede_id ?? "—"}`,
    },
    { key: "estado", header: "Estado", sortValue: (item) => item.estado, render: (item) => <StatusBadge status={item.estado} /> },
    {
      key: "progreso",
      header: "Progreso",
      sortValue: (item) => item.progreso,
      render: (item) => `${item.progreso ?? 0}%${item.etapa ? ` · ${item.etapa}` : ""}`,
    },
    {
      key: "aprobada",
      header: "Aprobada",
      sortValue: (item) => (item.aprobada ? 1 : 0),
      render: (item) => <StatusBadge status={item.aprobada ? "APROBADA" : "PENDIENTE"} />,
    },
    {
      key: "publicada",
      header: "Publicada",
      sortValue: (item) => (item.publicada ? 1 : 0),
      render: (item) => <StatusBadge status={item.publicada ? "PUBLICADA" : "PENDIENTE"} />,
    },
  ];

  return (
    <AppShell title="Corridas">
      <div className="space-y-6">
        <PageHeader title="Corridas" description="Solicita la generación de horarios para una sede y da seguimiento al proceso." />

        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(); }} className="poster-card space-y-4 p-5 sm:p-6">
          <div>
            <p className="type-kicker">Nueva corrida</p>
            <h2 className="mt-2 font-display text-3xl uppercase text-primary">Generar horarios</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-[0.8fr_1.2fr_auto] md:items-end">
            <div className="space-y-2">
              <Label htmlFor="corrida-sede">Sede</Label>
              <SearchableSelect
                id="corrida-sede"
                value={sedeId ? String(sedeId) : ""}
                onChange={(value) => setSedeId(Number(value))}
                options={(sedes || []).map((sede) => ({
                  value: String(sede.id),
                  label: sede.nombre,
                }))}
                placeholder="Selecciona una sede"
                searchPlaceholder="Buscar sede..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="corrida-grupos">IDs de grupos</Label>
              <Input id="corrida-grupos" placeholder="Ej. 1, 2, 3" value={grupoIds} onChange={(e) => setGrupoIds(e.target.value)} />
            </div>
            <Button type="submit" className="h-10" disabled={!sedeId || !grupoIds}>Crear corrida</Button>
          </div>
        </form>

        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin corridas" description="Crea la primera corrida para esta sede y espera el resultado del optimizador." />
        ) : (
          <DataTable
            columns={columns}
            data={data}
            isLoading={isLoading}
            keyExtractor={(item) => item.id}
            searchPlaceholder="Buscar por folio o sede"
            initialSort={{ key: "id", direction: "desc" }}
            filters={[
              {
                key: "sede_id",
                label: "Sede",
                options: (sedes || []).map((sede) => ({ value: String(sede.id), label: sede.nombre })),
                getValue: (item) => (item.sede_id ? String(item.sede_id) : ""),
              },
              {
                key: "estado",
                label: "Estado",
                options: [
                  { value: "PENDIENTE", label: "Pendiente" },
                  { value: "PROCESANDO", label: "Procesando" },
                  { value: "COMPLETADO", label: "Completado" },
                  { value: "ERROR", label: "Error" },
                ],
                getValue: (item) => item.estado,
              },
              {
                key: "publicada",
                label: "Publicación",
                options: [
                  { value: "true", label: "Publicadas" },
                  { value: "false", label: "Sin publicar" },
                ],
                getValue: (item) => String(item.publicada),
              },
            ]}
          />
        )}
      </div>
    </AppShell>
  );
}
