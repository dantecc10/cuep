"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { ImportDialog } from "@/components/shared/import-dialog";

interface User { id: number; nombre: string; apellido_paterno: string; email: string; es_tutor: boolean; }

export default function TutoresPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [importOpen, setImportOpen] = useState(false);
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
        <PageHeader
          title="Tutores"
          description="Personas que acompañan las asesorías del colectivo y su disponibilidad."
          actions={<Button variant="outline" onClick={() => setImportOpen(true)}>Importar CSV</Button>}
        />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin tutores" description="Cuando se registren tutores voluntarios aparecerán aquí para coordinar su carga docente." />
        ) : (
          <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />
        )}
        <ImportDialog
          entidad="usuarios"
          open={importOpen}
          onOpenChange={setImportOpen}
          onImported={() => {
            queryClient.invalidateQueries({ queryKey: ["tutores"] });
            queryClient.invalidateQueries({ queryKey: ["usuarios"] });
          }}
        />
      </div>
    </AppShell>
  );
}
