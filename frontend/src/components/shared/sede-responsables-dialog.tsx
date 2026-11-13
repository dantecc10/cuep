"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { apiErrorMessage } from "@/lib/api-error";
import { useDebouncedValue } from "@/lib/use-debounced-value";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface User {
  id: number;
  email: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string | null;
  role: string;
  sede_id: number | null;
}

interface Sede {
  id: number;
  nombre: string;
}

const roleLabels: Record<string, string> = {
  admin: "Admin",
  coordinador: "Coordinación",
  subcoordinador: "Subcoordinación",
  tutor: "Tutor",
  alumno: "Estudiante",
};

const RESPONSIBLE_ROLES = new Set(["coordinador", "subcoordinador"]);

export function SedeResponsablesDialog({
  open,
  onOpenChange,
  sede,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sede: Sede | null;
  onSaved?: () => void;
}) {
  const token = useAuthStore((state) => state.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search.trim(), 250);

  const { data: usuarios } = useQuery<User[]>({
    queryKey: ["usuarios", "sede-responsables", sede?.id],
    queryFn: async () => (await api.get("/usuarios", { headers, params: { sede_id: sede?.id } })).data,
    enabled: open && Boolean(sede?.id),
  });
  const { data: sedes } = useQuery<Sede[]>({
    queryKey: ["sedes"],
    queryFn: async () => (await api.get("/sedes", { headers })).data,
    enabled: open,
  });
  const { data: results, isFetching } = useQuery<User[]>({
    queryKey: ["usuarios", "sede-responsables-search", debouncedSearch],
    queryFn: async () =>
      (await api.get("/usuarios", { headers, params: { search: debouncedSearch || undefined } })).data,
    enabled: open && debouncedSearch.length > 0,
  });

  const sedeName = useMemo(
    () => new Map((sedes || []).map((item) => [item.id, item.nombre])),
    [sedes],
  );
  const responsables = useMemo(
    () => (usuarios || []).filter((item) => RESPONSIBLE_ROLES.has(item.role)),
    [usuarios],
  );

  const assignMutation = useMutation({
    mutationFn: async ({ user, role }: { user: User; role: "coordinador" | "subcoordinador" }) =>
      api.patch(
        `/usuarios/${user.id}`,
        { role, sede_id: sede?.id ?? null },
        { headers },
      ),
    onSuccess: (_, variables) => {
      toast.success(
        `${variables.user.nombre} ahora es ${roleLabels[variables.role]} de ${sede?.nombre || "la sede"}.`,
      );
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      queryClient.invalidateQueries({ queryKey: ["tutores"] });
      queryClient.invalidateQueries({ queryKey: ["sedes"] });
      onSaved?.();
    },
    onError: (error) => toast.error(apiErrorMessage(error, "No se pudo asignar el usuario.")),
  });

  function fullName(user: User) {
    return [user.nombre, user.apellido_paterno, user.apellido_materno]
      .filter(Boolean)
      .join(" ");
  }

  function assignmentHint(user: User) {
    if (!user.sede_id) return "Sin sede asignada";
    if (user.sede_id === sede?.id) return "Ya pertenece a esta sede";
    return `Actualmente en ${sedeName.get(user.sede_id) || `sede ${user.sede_id}`}; se moverá a esta sede`;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="max-w-3xl">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Responsables de {sede?.nombre || "la sede"}</DialogTitle>
          <DialogDescription>
            Busca por nombre o correo y asigna coordinación o subcoordinación. Si el usuario está en otra sede, se moverá a esta.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <section className="space-y-2">
            <p className="type-label text-ink/45">Responsables actuales</p>
            {responsables.length === 0 ? (
              <p className="border border-dashed border-ink/20 bg-sand/30 px-3 py-3 text-xs text-ink/55">
                Esta sede todavía no tiene coordinación asignada.
              </p>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {responsables.map((user) => (
                  <div key={user.id} className="border border-ink/15 bg-surface p-3">
                    <p className="text-sm font-semibold text-ink">{fullName(user)}</p>
                    <p className="text-xs text-ink/50">{user.email}</p>
                    <p className="mt-1 font-mono text-[0.56rem] uppercase tracking-[0.08em] text-primary">
                      {roleLabels[user.role] || user.role}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="space-y-2 border-t border-ink/10 pt-4">
            <p className="type-label text-ink/45">Buscar usuario</p>
            <label className="relative block">
              <Search
                aria-hidden="true"
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/40"
              />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Nombre, apellido o correo"
                className="w-full pl-9"
                autoFocus
              />
            </label>

            {debouncedSearch.length === 0 ? (
              <p className="flex items-center gap-2 px-1 py-3 text-xs text-ink/50">
                <UserPlus aria-hidden="true" className="h-4 w-4" />
                Escribe para buscar usuarios y asignarlos a esta sede.
              </p>
            ) : isFetching ? (
              <p className="px-1 py-3 text-xs text-ink/50">Buscando…</p>
            ) : (results || []).length === 0 ? (
              <p className="px-1 py-3 text-xs text-ink/50">No se encontraron usuarios.</p>
            ) : (
              <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                {(results || []).map((user) => (
                  <div key={user.id} className="border border-ink/15 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-ink">{fullName(user)}</p>
                        <p className="text-xs text-ink/50">{user.email}</p>
                        <p className="mt-1 font-mono text-[0.56rem] uppercase tracking-[0.06em] text-ink/45">
                          {roleLabels[user.role] || user.role} · {assignmentHint(user)}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => assignMutation.mutate({ user, role: "coordinador" })}
                          disabled={assignMutation.isPending}
                        >
                          Coordinación
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => assignMutation.mutate({ user, role: "subcoordinador" })}
                          disabled={assignMutation.isPending}
                        >
                          Subcoordinación
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </DialogContent>
    </Dialog>
  );
}
