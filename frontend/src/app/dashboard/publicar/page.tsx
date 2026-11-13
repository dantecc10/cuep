"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";

interface Corrida { id: number; sede_id: number | null; estado: string; aprobada: boolean; publicada: boolean; metricas_optimizacion: unknown; }
interface Sede { id: number; nombre: string; }

export default function PublicarPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<Corrida[]>({ queryKey: ["corridas"], queryFn: async () => (await api.get("/corridas", { headers })).data });
  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });
  const sedeName = new Map((sedes || []).map((sede) => [sede.id, sede.nombre]));

  const approveMutation = useMutation({ mutationFn: async (id: number) => api.post(`/corridas/${id}/aprobar`, {}, { headers }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }) });
  const publishMutation = useMutation({ mutationFn: async (id: number) => api.post(`/corridas/${id}/publicar`, {}, { headers }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }) });

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
      sortValue: (item) => (item.sede_id ? sedeName.get(item.sede_id) || "" : ""),
      render: (item) => (item.sede_id ? sedeName.get(item.sede_id) || `Sede ${item.sede_id}` : "Sin sede"),
    },
    { key: "estado", header: "Estado", sortValue: (item) => item.estado, render: (item) => <StatusBadge status={item.estado} /> },
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
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => approveMutation.mutate(item.id)} disabled={item.aprobada}>Aprobar</Button>
          <Button size="sm" onClick={() => publishMutation.mutate(item.id)} disabled={!item.aprobada || item.publicada}>Publicar</Button>
        </div>
      ),
    },
  ];

  return (
    <AppShell title="Publicar horarios">
      <div className="space-y-6">
        <PageHeader title="Publicar horarios" description="Revisa las corridas generadas, apruébalas y hazlas visibles para estudiantes y tutores." />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin corridas" description="Cuando se genere una corrida para tu sede aparecerá aquí para su aprobación." />
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
