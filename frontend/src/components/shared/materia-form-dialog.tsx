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

export interface MateriaFormValue {
  id?: number;
  nombre: string;
  nivel: string;
  area: string;
  descripcion: string;
}

export const emptyMateria: MateriaFormValue = {
  nombre: "",
  nivel: "PREPA",
  area: "",
  descripcion: "",
};

export function MateriaFormDialog({
  open,
  onOpenChange,
  materia,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  materia: MateriaFormValue | null;
  onSaved: () => void;
}) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();
  const [form, setForm] = useState<MateriaFormValue>(emptyMateria);

  useEffect(() => {
    if (open) {
      setForm(materia ? { ...materia } : { ...emptyMateria });
    }
  }, [open, materia]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        nombre: form.nombre,
        nivel: form.nivel,
        area: form.area,
        descripcion: form.descripcion || null,
      };
      const headers = { Authorization: `Bearer ${token}` };
      if (form.id) {
        return api.put(`/materias/${form.id}`, payload, { headers });
      }
      return api.post("/materias", payload, { headers });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materias"] });
      toast.success(form.id ? "Materia actualizada." : "Materia creada.");
      onSaved();
      onOpenChange(false);
    },
    onError: (error) => toast.error(apiErrorMessage(error, "No se pudo guardar la materia.")),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="max-w-2xl">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{form.id ? "Editar materia" : "Nueva materia"}</DialogTitle>
          <DialogDescription>Catálogo académico del colectivo.</DialogDescription>
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
              <Label htmlFor="materia-nombre">Nombre</Label>
              <Input
                id="materia-nombre"
                value={form.nombre}
                onChange={(event) => setForm({ ...form, nombre: event.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="materia-nivel">Nivel</Label>
              <select
                id="materia-nivel"
                className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={form.nivel}
                onChange={(event) => setForm({ ...form, nivel: event.target.value })}
              >
                <option value="PREPA">Preparatoria</option>
                <option value="LICENCIATURA">Licenciatura</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="materia-area">Área</Label>
              <Input
                id="materia-area"
                value={form.area}
                onChange={(event) => setForm({ ...form, area: event.target.value })}
                required
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="materia-descripcion">Descripción</Label>
              <Input
                id="materia-descripcion"
                value={form.descripcion}
                onChange={(event) => setForm({ ...form, descripcion: event.target.value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={!form.nombre || !form.area || mutation.isPending}>
              {mutation.isPending ? "Guardando..." : form.id ? "Guardar cambios" : "Crear materia"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
