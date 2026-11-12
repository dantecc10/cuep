"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
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

export interface PlanFormValue {
  id?: number;
  nombre: string;
  nivel: string;
  area: string;
  descripcion: string;
  activo: boolean;
}

const empty: PlanFormValue = {
  nombre: "",
  nivel: "PREPA",
  area: "",
  descripcion: "",
  activo: true,
};

export function PlanFormDialog({
  open,
  onOpenChange,
  plan,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  plan: PlanFormValue | null;
  onSaved: () => void;
}) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();
  const [form, setForm] = useState<PlanFormValue>(empty);

  useEffect(() => {
    if (open) {
      setForm(plan ? { ...plan } : { ...empty });
    }
  }, [open, plan]);

  const mutation = useMutation({
    mutationFn: async () => {
      const headers = { Authorization: `Bearer ${token}` };
      const payload = {
        nombre: form.nombre,
        nivel: form.nivel,
        area: form.area || null,
        descripcion: form.descripcion || null,
      };
      if (form.id) {
        return api.put(`/planes/${form.id}`, { ...payload, activo: form.activo }, { headers });
      }
      return api.post("/planes", payload, { headers });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["planes"] });
      toast.success(form.id ? "Plan actualizado." : "Plan creado.");
      onSaved();
      onOpenChange(false);
    },
    onError: (error) => toast.error(apiErrorMessage(error, "No se pudo guardar el plan.")),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="max-w-2xl">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{form.id ? "Editar plan de estudios" : "Nuevo plan de estudios"}</DialogTitle>
          <DialogDescription>Define el plan y después asigna sus materias.</DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate();
          }}
          className="space-y-4"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="plan-nombre">Nombre</Label>
              <Input
                id="plan-nombre"
                value={form.nombre}
                onChange={(event) => setForm({ ...form, nombre: event.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="plan-nivel">Nivel</Label>
              <select
                id="plan-nivel"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={form.nivel}
                onChange={(event) => setForm({ ...form, nivel: event.target.value })}
              >
                <option value="PREPA">Preparatoria</option>
                <option value="LICENCIATURA">Licenciatura</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="plan-area">Área</Label>
              <Input
                id="plan-area"
                value={form.area}
                onChange={(event) => setForm({ ...form, area: event.target.value })}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="plan-descripcion">Descripción</Label>
              <Input
                id="plan-descripcion"
                value={form.descripcion}
                onChange={(event) => setForm({ ...form, descripcion: event.target.value })}
              />
            </div>
            {form.id && (
              <label className="flex items-center gap-2 text-sm md:col-span-2">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[#A92730]"
                  checked={form.activo}
                  onChange={(event) => setForm({ ...form, activo: event.target.checked })}
                />
                <span className="text-ink/70">Plan activo</span>
              </label>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={!form.nombre || mutation.isPending}>
              {mutation.isPending ? "Guardando..." : form.id ? "Guardar cambios" : "Crear plan"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
