"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

interface User { id: number; email: string; nombre: string; apellido_paterno: string; role: string; sede_id: number | null; es_tutor: boolean; is_active: boolean; }

export default function UsuariosPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { data } = useQuery<User[]>({ queryKey: ["usuarios"], queryFn: async () => (await api.get("/usuarios", { headers })).data });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: Record<string, unknown> }) => api.patch(`/usuarios/${id}`, payload, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["usuarios"] }),
  });

  return (
    <AppShell title="Usuarios">
      <div className="space-y-3">
        {(data || []).map((u) => (
          <div key={u.id} className="border border-primary bg-surface rounded-card p-3 space-y-2">
            <p className="font-semibold">{u.nombre} {u.apellido_paterno} — {u.email}</p>
            <div className="flex flex-wrap gap-2">
              <select className="border border-primary rounded-button p-2 bg-surface" value={u.role} onChange={(e) => updateMutation.mutate({ id: u.id, payload: { role: e.target.value } })}>
                <option value="admin">admin</option>
                <option value="coordinador">coordinador</option>
                <option value="subcoordinador">subcoordinador</option>
                <option value="tutor">tutor</option>
                <option value="alumno">alumno</option>
              </select>
              <Input className="w-24" type="number" placeholder="Sede" defaultValue={u.sede_id ?? ""} onBlur={(e) => updateMutation.mutate({ id: u.id, payload: { sede_id: e.target.value ? Number(e.target.value) : null } })} />
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={u.es_tutor} onChange={(e) => updateMutation.mutate({ id: u.id, payload: { es_tutor: e.target.checked } })} /> Tutor</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={u.is_active} onChange={(e) => updateMutation.mutate({ id: u.id, payload: { is_active: e.target.checked } })} /> Activo</label>
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
