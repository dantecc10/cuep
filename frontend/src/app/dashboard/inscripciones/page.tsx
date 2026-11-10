"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/ui/empty-state";

interface Enrollment { id: number; student_id: number; grupo_id: number; estado: string; payment_status: string; }

export default function InscripcionesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { data } = useQuery<Enrollment[]>({ queryKey: ["enrollments"], queryFn: async () => (await api.get("/enrollments", { headers })).data });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Record<string, unknown> }) => api.patch(`/enrollments/${id}`, payload, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["enrollments"] }),
  });

  return (
    <AppShell title="Inscripciones">
      <div className="space-y-4">
        <PageHeader title="Inscripciones" description="Cupos, lista de espera y pagos." />
        {(data || []).length === 0 && <EmptyState title="Sin inscripciones" description="No hay inscripciones registradas." />}
        {(data || []).map((e) => (
          <div key={e.id} className="border border-primary bg-surface rounded-card p-3 flex flex-wrap items-center gap-2">
            <span className="font-semibold">#{e.id}</span>
            <span>Alumno {e.student_id} — Grupo {e.grupo_id}</span>
            <span>{e.estado} / {e.payment_status}</span>
            <select className="border border-primary rounded-button p-1 bg-surface" value={e.estado} onChange={(ev) => updateMutation.mutate({ id: e.id, payload: { estado: ev.target.value } })}>
              <option value="confirmada">confirmada</option>
              <option value="pendiente_pago">pendiente_pago</option>
              <option value="lista_espera">lista_espera</option>
              <option value="cancelada">cancelada</option>
            </select>
            <Button size="sm" variant="outline" onClick={() => updateMutation.mutate({ id: e.id, payload: { payment_status: "pagado" } })}>Marcar pagado</Button>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
