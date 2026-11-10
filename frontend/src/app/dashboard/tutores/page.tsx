"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";

interface User { id: number; nombre: string; apellido_paterno: string; email: string; es_tutor: boolean; }

export default function TutoresPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const { data, isLoading } = useQuery<User[]>({ queryKey: ["tutores"], queryFn: async () => (await api.get("/tutores", { headers })).data });

  const columns: Column<User>[] = [
    {
      key: "nombre",
      header: "Tutor",
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.nombre} {item.apellido_paterno}</p>
          <p className="text-xs text-ink/50">{item.email}</p>
        </div>
      ),
    },
    {
      key: "es_tutor",
      header: "Carga docente",
      render: (item) => <StatusBadge status={item.es_tutor ? "PUBLICADA" : "PENDIENTE"} />,
    },
  ];

  return (
    <AppShell title="Tutores">
      <div className="space-y-6">
        <PageHeader title="Tutores" description="Personas que acompañan las asesorías del colectivo y su disponibilidad." />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin tutores" description="Cuando se registren tutores voluntarios aparecerán aquí para coordinar su carga docente." />
        ) : (
          <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />
        )}
      </div>
    </AppShell>
  );
}
