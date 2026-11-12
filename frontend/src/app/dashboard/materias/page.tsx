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
import { MateriaFormDialog, type MateriaFormValue } from "@/components/shared/materia-form-dialog";
import { ImportDialog } from "@/components/shared/import-dialog";

interface Materia {
  id: number;
  nombre: string;
  nivel: string;
  area: string;
  descripcion: string | null;
}

function toFormValue(materia: Materia): MateriaFormValue {
  return {
    id: materia.id,
    nombre: materia.nombre,
    nivel: materia.nivel,
    area: materia.area,
    descripcion: materia.descripcion || "",
  };
}

export default function MateriasPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { confirm, dialog } = useConfirmDialog();
  const [formOpen, setFormOpen] = useState(false);
  const [editingMateria, setEditingMateria] = useState<MateriaFormValue | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  const { data, isLoading } = useQuery<Materia[]>({
    queryKey: ["materias"],
    queryFn: async () => (await api.get("/materias", { headers })).data,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => api.delete(`/materias/${id}`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["materias"] }),
  });

  const columns: Column<Materia>[] = [
    {
      key: "nombre",
      header: "Materia",
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.nombre}</p>
          {item.descripcion && <p className="mt-0.5 max-w-md text-xs text-ink/55">{item.descripcion}</p>}
        </div>
      ),
    },
    { key: "nivel", header: "Nivel", render: (item) => (item.nivel === "PREPA" ? "Preparatoria" : "Licenciatura") },
    { key: "area", header: "Área" },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <div className="flex justify-end gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setEditingMateria(toFormValue(item));
              setFormOpen(true);
            }}
          >
            Editar
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={async () => {
              if (await confirm({ title: "Eliminar materia", description: `¿Eliminar ${item.nombre} del catálogo?` })) {
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
    <AppShell title="Materias">
      <div className="space-y-6">
        <PageHeader
          title="Materias"
          description="Catálogo académico que alimenta los planes de estudio y las asesorías."
          actions={
            <>
              <Button
                onClick={() => {
                  setEditingMateria(null);
                  setFormOpen(true);
                }}
              >
                Nueva materia
              </Button>
              <Button variant="outline" onClick={() => setImportOpen(true)}>
                Importar CSV
              </Button>
            </>
          }
        />

        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin materias" description="Agrega la primera materia del catálogo para comenzar a armar planes y grupos." />
        ) : (
          <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />
        )}

        <MateriaFormDialog
          open={formOpen}
          onOpenChange={setFormOpen}
          materia={editingMateria}
          onSaved={() => setEditingMateria(null)}
        />
        <ImportDialog
          entidad="materias"
          open={importOpen}
          onOpenChange={setImportOpen}
          onImported={() => queryClient.invalidateQueries({ queryKey: ["materias"] })}
        />
        {dialog}
      </div>
    </AppShell>
  );
}
