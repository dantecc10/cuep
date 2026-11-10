"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";

interface User { id: number; email: string; nombre: string; apellido_paterno: string; role: string; sede_id: number | null; es_tutor: boolean; is_active: boolean; }

const roleLabels: Record<string, string> = {
  admin: "Admin",
  coordinador: "Coordinación",
  subcoordinador: "Subcoordinación",
  tutor: "Tutor",
  alumno: "Estudiante",
};

export default function UsuariosPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<User[]>({ queryKey: ["usuarios"], queryFn: async () => (await api.get("/usuarios", { headers })).data });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Record<string, unknown> }) => api.patch(`/usuarios/${id}`, payload, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["usuarios"] }),
  });

  const columns: Column<User>[] = [
    {
      key: "usuario",
      header: "Usuario",
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
      render: (item) => (
        <select
          aria-label={`Rol de ${item.nombre}`}
          className="h-8 border border-ink/30 bg-surface px-2 font-mono text-[0.62rem] font-semibold uppercase tracking-[0.06em] text-ink outline-none focus-visible:border-primary"
          value={item.role}
          onChange={(e) => updateMutation.mutate({ id: item.id, payload: { role: e.target.value } })}
        >
          {Object.entries(roleLabels).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      ),
    },
    {
      key: "sede_id",
      header: "Sede",
      render: (item) => (
        <Input
          className="h-8 w-20"
          type="number"
          defaultValue={item.sede_id ?? ""}
          aria-label={`Sede de ${item.nombre}`}
          onBlur={(e) => updateMutation.mutate({ id: item.id, payload: { sede_id: e.target.value ? Number(e.target.value) : null } })}
        />
      ),
    },
    {
      key: "es_tutor",
      header: "Tutor",
      render: (item) => (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            className="h-4 w-4 accent-[#A92730]"
            checked={item.es_tutor}
            onChange={(e) => updateMutation.mutate({ id: item.id, payload: { es_tutor: e.target.checked } })}
          />
          <span className="text-xs text-ink/60">{item.es_tutor ? "Sí" : "No"}</span>
        </label>
      ),
    },
    {
      key: "is_active",
      header: "Estado",
      render: (item) => (
        <button type="button" onClick={() => updateMutation.mutate({ id: item.id, payload: { is_active: !item.is_active } })}>
          <StatusBadge status={item.is_active ? "PUBLICADA" : "PENDIENTE"} />
        </button>
      ),
    },
  ];

  return (
    <AppShell title="Usuarios">
      <div className="space-y-6">
        <PageHeader title="Usuarios" description="Roles, sedes y permisos de las personas que sostienen el colectivo." />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin usuarios" description="No hay usuarios registrados todavía." />
        ) : (
          <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => item.id} />
        )}
      </div>
    </AppShell>
  );
}
