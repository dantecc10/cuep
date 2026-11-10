"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";

interface Corrida { id: number; sede_id: number | null; estado: string; aprobada: boolean; publicada: boolean; progreso: number; etapa: string | null; }

export default function CorridasPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [sedeId, setSedeId] = useState(1);
  const [grupoIds, setGrupoIds] = useState("1");

  const { data, isLoading } = useQuery<Corrida[]>({ queryKey: ["corridas"], queryFn: async () => (await api.get("/corridas", { headers })).data, refetchInterval: 3000 });
  const createMutation = useMutation({ mutationFn: async () => api.post("/corridas", { sede_id: sedeId, grupo_ids: grupoIds.split(",").map((x) => Number(x.trim())).filter(Boolean) }, { headers }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }) });

  const columns: Column<Corrida>[] = [
    { key: "id", header: "ID" },
    { key: "sede_id", header: "Sede" },
    { key: "estado", header: "Estado" },
    { key: "progreso", header: "Progreso", render: (item) => `${item.progreso ?? 0}% ${item.etapa ? `— ${item.etapa}` : ""}` },
    { key: "aprobada", header: "Aprobada", render: (item) => (item.aprobada ? "Sí" : "No") },
    { key: "publicada", header: "Publicada", render: (item) => (item.publicada ? "Sí" : "No") },
  ];

  return (
    <AppShell title="Corridas">
      <div className="space-y-6">
        <PageHeader title="Corridas" description="Solicita y consulta generaciones de horarios." />
        <div className="flex flex-wrap gap-2">
          <input className="border border-primary rounded-button p-2 bg-surface" type="number" value={sedeId} onChange={(e) => setSedeId(Number(e.target.value))} />
          <input className="border border-primary rounded-button p-2 bg-surface flex-1" placeholder="IDs de grupos, ej. 1,2" value={grupoIds} onChange={(e) => setGrupoIds(e.target.value)} />
          <button className="btn-primary" onClick={() => createMutation.mutate()}>Crear corrida</button>
        </div>
        {!isLoading && (!data || data.length === 0) ? <EmptyState title="Sin corridas" description="Crea la primera corrida para esta sede." /> : <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />}
      </div>
    </AppShell>
  );
}
