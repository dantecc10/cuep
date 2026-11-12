"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { useConfirmDialog } from "@/components/shared/confirm-dialog";
import { SedeFormDialog, type SedeFormValue } from "@/components/shared/sede-form-dialog";
import { ImportDialog } from "@/components/shared/import-dialog";

interface Sede {
  id: number;
  nombre: string;
  ciudad: string | null;
  codigo: string | null;
  descripcion: string | null;
  maps_url: string | null;
  image_url: string | null;
  activo: boolean;
}

function toFormValue(sede: Sede): SedeFormValue {
  return {
    id: sede.id,
    nombre: sede.nombre,
    ciudad: sede.ciudad || "",
    codigo: sede.codigo || "",
    descripcion: sede.descripcion || "",
    maps_url: sede.maps_url || "",
    image_url: sede.image_url || "",
    activo: sede.activo,
  };
}

export default function SedesPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { confirm, dialog } = useConfirmDialog();
  const [formOpen, setFormOpen] = useState(false);
  const [editingSede, setEditingSede] = useState<SedeFormValue | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  const { data, isLoading } = useQuery<Sede[]>({
    queryKey: ["sedes"],
    queryFn: async () => (await api.get("/sedes", { headers })).data,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/sedes/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sedes"] }),
  });

  const columns: Column<Sede>[] = [
    { key: "nombre", header: "Nombre" },
    { key: "codigo", header: "Código" },
    { key: "ciudad", header: "Ciudad" },
    { key: "activo", header: "Activo", render: (item) => (item.activo ? "Sí" : "No") },
    {
      key: "acciones",
      header: "Acciones",
      render: (item) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setEditingSede(toFormValue(item));
              setFormOpen(true);
            }}
          >
            Editar
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              if (await confirm({ title: "Eliminar sede", description: "¿Eliminar esta sede?" })) {
                deleteMutation.mutate(item.id);
              }
            }}
          >
            Eliminar
          </Button>
        </div>
      ),
    },
  ];

  return (
    <AppShell title="">
      <div className="space-y-6">
        <PageHeader
          title="Sedes"
          description="Gestión de sedes del colectivo."
          actions={
            <>
              <Button
                onClick={() => {
                  setEditingSede(null);
                  setFormOpen(true);
                }}
              >
                Nueva sede
              </Button>
              <Button variant="outline" onClick={() => setImportOpen(true)}>
                Importar CSV
              </Button>
            </>
          }
        />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin sedes" description="Crea la primera sede del colectivo." />
        ) : (
          <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />
        )}
        <SedeFormDialog
          open={formOpen}
          onOpenChange={setFormOpen}
          sede={editingSede}
          onSaved={() => setEditingSede(null)}
        />
        <ImportDialog
          entidad="sedes"
          open={importOpen}
          onOpenChange={setImportOpen}
          onImported={() => queryClient.invalidateQueries({ queryKey: ["sedes"] })}
        />
        {dialog}
      </div>
    </AppShell>
  );
}
