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
import { UserFormDialog, type UserFormValue } from "@/components/shared/user-form-dialog";
import { ImportDialog } from "@/components/shared/import-dialog";

interface User {
  id: number;
  email: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string | null;
  role: string;
  sede_id: number | null;
  es_tutor: boolean;
  is_active: boolean;
  telefono: string | null;
  area_principal: string | null;
  carga_max_horas: number;
}
interface Sede {
  id: number;
  nombre: string;
  ciudad: string | null;
}

const roleLabels: Record<string, string> = {
  admin: "Admin",
  coordinador: "Coordinación",
  subcoordinador: "Subcoordinación",
  tutor: "Tutor",
  alumno: "Estudiante",
};

function toFormValue(user: User): UserFormValue {
  return {
    id: user.id,
    email: user.email,
    nombre: user.nombre,
    apellido_paterno: user.apellido_paterno,
    apellido_materno: user.apellido_materno || "",
    role: user.role,
    sede_id: user.sede_id,
    es_tutor: user.es_tutor,
    is_active: user.is_active,
    telefono: user.telefono || "",
    area_principal: user.area_principal || "",
    carga_max_horas: user.carga_max_horas || 0,
  };
}

export default function UsuariosPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserFormValue | null>(null);
  const [importOpen, setImportOpen] = useState(false);

  const { data, isLoading } = useQuery<User[]>({ queryKey: ["usuarios"], queryFn: async () => (await api.get("/usuarios", { headers })).data });
  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });
  const sedeName = new Map((sedes || []).map((sede) => [sede.id, sede.nombre]));

  const columns: Column<User>[] = [
    {
      key: "usuario",
      header: "Usuario",
      sortValue: (item) => `${item.nombre} ${item.apellido_paterno}`,
      searchValue: (item) =>
        [item.nombre, item.apellido_paterno, item.apellido_materno, item.email]
          .filter(Boolean)
          .join(" "),
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.nombre} {item.apellido_paterno}</p>
          <p className="text-xs text-ink/50">{item.email}</p>
        </div>
      ),
    },
    {
      key: "role",
      header: "Rol",
      sortValue: (item) => item.role,
      render: (item) => (
        <span className="font-mono text-[0.62rem] font-semibold uppercase tracking-[0.06em] text-ink/70">
          {roleLabels[item.role] || item.role}
        </span>
      ),
    },
    {
      key: "sede_id",
      header: "Sede",
      sortValue: (item) => (item.sede_id ? sedeName.get(item.sede_id) || "" : ""),
      render: (item) => (
        <span className="text-xs text-ink/60">
          {item.sede_id ? sedeName.get(item.sede_id) || `Sede ${item.sede_id}` : "Sin sede"}
        </span>
      ),
    },
    {
      key: "es_tutor",
      header: "Tutor",
      sortValue: (item) => (item.es_tutor ? 1 : 0),
      render: (item) => <span className="text-xs text-ink/60">{item.es_tutor ? "Sí" : "No"}</span>,
    },
    {
      key: "is_active",
      header: "Estado",
      sortValue: (item) => (item.is_active ? 1 : 0),
      render: (item) => <StatusBadge status={item.is_active ? "PUBLICADA" : "PENDIENTE"} />,
    },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            setEditingUser(toFormValue(item));
            setFormOpen(true);
          }}
        >
          Editar
        </Button>
      ),
    },
  ];

  return (
    <AppShell title="Usuarios">
      <div className="space-y-6">
        <PageHeader
          title="Usuarios"
          description="Roles, sedes y permisos de las personas que sostienen el colectivo."
          actions={
            <>
              <Button
                onClick={() => {
                  setEditingUser(null);
                  setFormOpen(true);
                }}
              >
                Nuevo usuario
              </Button>
              <Button variant="outline" onClick={() => setImportOpen(true)}>
                Importar CSV
              </Button>
            </>
          }
        />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin usuarios" description="No hay usuarios registrados todavía." />
        ) : (
          <DataTable
            columns={columns}
            data={data}
            isLoading={isLoading}
            keyExtractor={(item) => item.id}
            searchPlaceholder="Buscar por nombre o correo"
            initialSort={{ key: "usuario", direction: "asc" }}
            filters={[
              {
                key: "role",
                label: "Rol",
                options: Object.entries(roleLabels).map(([value, label]) => ({ value, label })),
                getValue: (item) => item.role,
              },
              {
                key: "sede_id",
                label: "Sede",
                options: (sedes || []).map((sede) => ({ value: String(sede.id), label: sede.nombre })),
                getValue: (item) => (item.sede_id ? String(item.sede_id) : ""),
              },
              {
                key: "es_tutor",
                label: "Tutor",
                options: [
                  { value: "true", label: "Sí" },
                  { value: "false", label: "No" },
                ],
                getValue: (item) => String(item.es_tutor),
              },
              {
                key: "is_active",
                label: "Estado",
                options: [
                  { value: "true", label: "Activo" },
                  { value: "false", label: "Inactivo" },
                ],
                getValue: (item) => String(item.is_active),
              },
            ]}
          />
        )}
        <UserFormDialog
          open={formOpen}
          onOpenChange={setFormOpen}
          user={editingUser}
          onSaved={() => setEditingUser(null)}
        />
        <ImportDialog
          entidad="usuarios"
          open={importOpen}
          onOpenChange={setImportOpen}
          onImported={() => {
            queryClient.invalidateQueries({ queryKey: ["usuarios"] });
            queryClient.invalidateQueries({ queryKey: ["tutores"] });
          }}
        />
      </div>
    </AppShell>
  );
}
