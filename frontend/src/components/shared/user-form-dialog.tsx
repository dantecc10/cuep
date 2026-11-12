"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { apiErrorMessage } from "@/lib/api-error";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export interface UserFormValue {
  id?: number;
  email: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string;
  role: string;
  sede_id: number | null;
  es_tutor: boolean;
  is_active: boolean;
  telefono: string;
  area_principal: string;
  carga_max_horas: number;
}

interface Sede {
  id: number;
  nombre: string;
}

const empty: UserFormValue = {
  email: "",
  nombre: "",
  apellido_paterno: "",
  apellido_materno: "",
  role: "tutor",
  sede_id: null,
  es_tutor: true,
  is_active: true,
  telefono: "",
  area_principal: "",
  carga_max_horas: 0,
};

const roleLabels: Record<string, string> = {
  admin: "Admin",
  coordinador: "Coordinación",
  subcoordinador: "Subcoordinación",
  tutor: "Tutor",
  alumno: "Estudiante",
};

export function UserFormDialog({
  open,
  onOpenChange,
  user,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: UserFormValue | null;
  onSaved: () => void;
}) {
  const token = useAuthStore((state) => state.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [form, setForm] = useState<UserFormValue>(empty);
  const [password, setPassword] = useState("");

  const { data: sedes } = useQuery<Sede[]>({
    queryKey: ["sedes"],
    queryFn: async () => (await api.get("/sedes", { headers })).data,
    enabled: open,
  });

  useEffect(() => {
    if (open) {
      setForm(user ? { ...user } : { ...empty });
      setPassword("");
    }
  }, [open, user]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        email: form.email,
        nombre: form.nombre,
        apellido_paterno: form.apellido_paterno,
        apellido_materno: form.apellido_materno || null,
        role: form.role,
        sede_id: form.sede_id,
        es_tutor: form.es_tutor,
        telefono: form.telefono || null,
        area_principal: form.area_principal || null,
        carga_max_horas: form.carga_max_horas,
      };
      if (form.id) {
        return api.patch(
          `/usuarios/${form.id}`,
          { ...payload, is_active: form.is_active },
          { headers },
        );
      }
      return api.post("/usuarios", { ...payload, password }, { headers });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
      queryClient.invalidateQueries({ queryKey: ["tutores"] });
      toast.success(form.id ? "Usuario actualizado." : "Usuario creado.");
      onSaved();
      onOpenChange(false);
    },
    onError: (error) => toast.error(apiErrorMessage(error, "No se pudo guardar el usuario.")),
  });

  const isEditing = Boolean(form.id);

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="max-w-3xl">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "Editar usuario" : "Nuevo usuario"}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Actualiza los datos, rol y sede del usuario."
              : "Crea una cuenta con contraseña inicial."}
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="user-email">Email</Label>
              <Input
                id="user-email"
                type="email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
                required
              />
            </div>
            {!isEditing && (
              <div className="space-y-2">
                <Label htmlFor="user-password">Contraseña inicial</Label>
                <Input
                  id="user-password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={6}
                  required
                />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="user-nombre">Nombre</Label>
              <Input
                id="user-nombre"
                value={form.nombre}
                onChange={(event) => setForm({ ...form, nombre: event.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-apellido-paterno">Apellido paterno</Label>
              <Input
                id="user-apellido-paterno"
                value={form.apellido_paterno}
                onChange={(event) => setForm({ ...form, apellido_paterno: event.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-apellido-materno">Apellido materno</Label>
              <Input
                id="user-apellido-materno"
                value={form.apellido_materno}
                onChange={(event) => setForm({ ...form, apellido_materno: event.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-role">Rol</Label>
              <select
                id="user-role"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={form.role}
                onChange={(event) => {
                  const role = event.target.value;
                  setForm({
                    ...form,
                    role,
                    es_tutor: role === "tutor" ? true : form.es_tutor,
                  });
                }}
              >
                {Object.entries(roleLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-sede">Sede</Label>
              <select
                id="user-sede"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={form.sede_id ?? ""}
                onChange={(event) =>
                  setForm({
                    ...form,
                    sede_id: event.target.value ? Number(event.target.value) : null,
                  })
                }
              >
                <option value="">Sin sede</option>
                {(sedes || []).map((sede) => (
                  <option key={sede.id} value={sede.id}>
                    {sede.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-telefono">Teléfono</Label>
              <Input
                id="user-telefono"
                value={form.telefono}
                onChange={(event) => setForm({ ...form, telefono: event.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-area">Área principal</Label>
              <Input
                id="user-area"
                value={form.area_principal}
                onChange={(event) => setForm({ ...form, area_principal: event.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-carga">Carga máxima (horas)</Label>
              <Input
                id="user-carga"
                type="number"
                min={0}
                value={form.carga_max_horas}
                onChange={(event) =>
                  setForm({ ...form, carga_max_horas: Number(event.target.value) || 0 })
                }
              />
            </div>
            <label className="flex items-center gap-2 self-end text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 accent-[#A92730]"
                checked={form.es_tutor}
                onChange={(event) => setForm({ ...form, es_tutor: event.target.checked })}
              />
              <span className="text-ink/70">Imparte clases (tutor)</span>
            </label>
            {isEditing && (
              <label className="flex items-center gap-2 text-sm md:col-span-2">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[#A92730]"
                  checked={form.is_active}
                  onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
                />
                <span className="text-ink/70">Cuenta activa</span>
              </label>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={
                !form.email ||
                !form.nombre ||
                !form.apellido_paterno ||
                (!isEditing && password.length < 6) ||
                mutation.isPending
              }
            >
              {mutation.isPending ? "Guardando..." : isEditing ? "Guardar cambios" : "Crear usuario"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
