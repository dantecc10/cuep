"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/ui/empty-state";

interface Corrida { id: number; sede_id: number | null; estado: string; aprobada: boolean; publicada: boolean; metricas_optimizacion: unknown; }

export default function PublicarPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { data } = useQuery<Corrida[]>({ queryKey: ["corridas"], queryFn: async () => (await api.get("/corridas", { headers })).data });

  const approveMutation = useMutation({ mutationFn: async (id: number) => api.post(`/corridas/${id}/aprobar`, {}, { headers }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }) });
  const publishMutation = useMutation({ mutationFn: async (id: number) => api.post(`/corridas/${id}/publicar`, {}, { headers }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }) });

  return (
    <AppShell title="Publicar horarios">
      <div className="space-y-4">
        <PageHeader title="Publicar horarios" description="Aprueba y publica combinaciones por sede." />
        {(data || []).length === 0 && <EmptyState title="Sin corridas" description="No hay corridas disponibles." />}
        {(data || []).map((c) => (
          <div key={c.id} className="border border-primary bg-surface rounded-card p-3 space-y-2">
            <p className="font-semibold">Corrida #{c.id} — sede {c.sede_id} — {c.estado}</p>
            <p className="text-sm">Aprobada: {String(c.aprobada)} | Publicada: {String(c.publicada)}</p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => approveMutation.mutate(c.id)} disabled={c.aprobada}>Aprobar</Button>
              <Button size="sm" onClick={() => publishMutation.mutate(c.id)} disabled={!c.aprobada || c.publicada}>Publicar</Button>
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
