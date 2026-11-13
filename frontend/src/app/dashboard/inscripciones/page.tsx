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

interface Enrollment {
  id: number;
  student_id: number;
  grupo_id: number;
  estado: string;
  payment_status: string;
  student_name: string | null;
  student_matricula: string | null;
  grupo_name: string | null;
  materia_name: string | null;
}

export default function InscripcionesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<Enrollment[]>({ queryKey: ["enrollments"], queryFn: async () => (await api.get("/enrollments", { headers })).data });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Record<string, unknown> }) => api.patch(`/enrollments/${id}`, payload, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["enrollments"] }),
  });

  const columns: Column<Enrollment>[] = [
    {
      key: "id",
      header: "Folio",
      sortValue: (item) => item.id,
      render: (item) => <span className="font-mono text-xs font-bold">#{item.id}</span>,
    },
    {
      key: "estudiante",
      header: "Alumno / grupo",
      sortValue: (item) => item.student_name || "",
      searchValue: (item) =>
        [
          item.student_name,
          item.student_matricula,
          item.materia_name,
          item.grupo_name,
        ]
          .filter(Boolean)
          .join(" "),
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.student_name || `Alumno #${item.student_id}`}</p>
          <p className="text-xs text-ink/50">
            {item.student_matricula ? `${item.student_matricula} · ` : ""}
            {item.materia_name || "Materia sin nombre"} · {item.grupo_name || `Grupo #${item.grupo_id}`}
          </p>
        </div>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      sortValue: (item) => item.estado,
      render: (item) => (
        <select
          aria-label={`Estado de inscripción ${item.id}`}
          className="h-8 border border-ink/30 bg-surface px-2 font-mono text-[0.62rem] font-semibold uppercase tracking-[0.06em] text-ink outline-none focus-visible:border-primary"
          value={item.estado}
          onChange={(e) => updateMutation.mutate({ id: item.id, payload: { estado: e.target.value } })}
        >
          <option value="confirmada">Confirmada</option>
          <option value="pendiente_pago">Pendiente de pago</option>
          <option value="lista_espera">Lista de espera</option>
          <option value="cancelada">Cancelada</option>
        </select>
      ),
    },
    {
      key: "payment_status",
      header: "Pago",
      sortValue: (item) => item.payment_status,
      render: (item) => <StatusBadge status={item.payment_status === "pagado" ? "confirmada" : item.payment_status} />,
    },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <Button size="sm" variant="outline" onClick={() => updateMutation.mutate({ id: item.id, payload: { payment_status: "pagado" } })} disabled={item.payment_status === "pagado"}>
          Marcar pagado
        </Button>
      ),
    },
  ];

  return (
    <AppShell title="Inscripciones">
      <div className="space-y-6">
        <PageHeader title="Inscripciones" description="Cupos, lista de espera y pagos de las personas inscritas al colectivo." />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin inscripciones" description="Cuando las y los estudiantes elijan sus grupos, las inscripciones aparecerán aquí." />
        ) : (
          <DataTable
            columns={columns}
            data={data}
            isLoading={isLoading}
            keyExtractor={(item) => item.id}
            searchPlaceholder="Buscar alumno, matrícula, materia o grupo"
            initialSort={{ key: "id", direction: "desc" }}
            filters={[
              {
                key: "estado",
                label: "Estado",
                options: [
                  { value: "confirmada", label: "Confirmada" },
                  { value: "pendiente_pago", label: "Pendiente de pago" },
                  { value: "lista_espera", label: "Lista de espera" },
                  { value: "cancelada", label: "Cancelada" },
                ],
                getValue: (item) => item.estado,
              },
              {
                key: "payment_status",
                label: "Pago",
                options: [
                  { value: "pagado", label: "Pagado" },
                  { value: "pendiente", label: "Pendiente" },
                  { value: "no_requerido", label: "No requerido" },
                ],
                getValue: (item) => item.payment_status,
              },
            ]}
          />
        )}
      </div>
    </AppShell>
  );
}
