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

export interface SedeFormValue {
  id?: number;
  nombre: string;
  ciudad: string;
  codigo: string;
  descripcion: string;
  maps_url: string;
  image_url: string;
  activo: boolean;
}

const empty: SedeFormValue = {
  nombre: "",
  ciudad: "",
  codigo: "",
  descripcion: "",
  maps_url: "",
  image_url: "",
  activo: true,
};

export function SedeFormDialog({
  open,
  onOpenChange,
  sede,
  onSaved,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  sede: SedeFormValue | null;
  onSaved: () => void;
}) {
  const token = useAuthStore((state) => state.token);
  const queryClient = useQueryClient();
  const [form, setForm] = useState<SedeFormValue>(empty);

  useEffect(() => {
    if (open) {
      setForm(sede ? { ...sede } : { ...empty });
    }
  }, [open, sede]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        nombre: form.nombre,
        ciudad: form.ciudad || null,
        codigo: form.codigo,
        descripcion: form.descripcion || null,
        maps_url: form.maps_url || null,
        image_url: form.image_url || null,
        activo: form.activo,
      };
      if (form.id) {
        return api.put(`/sedes/${form.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      return api.post("/sedes", payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sedes"] });
      toast.success(form.id ? "Sede actualizada." : "Sede creada.");
      onSaved();
      onOpenChange(false);
    },
    onError: (error) => toast.error(apiErrorMessage(error, "No se pudo guardar la sede.")),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="max-w-2xl">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{form.id ? "Editar sede" : "Nueva sede"}</DialogTitle>
          <DialogDescription>Datos de la sede del colectivo.</DialogDescription>
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
              <Label htmlFor="sede-nombre">Nombre</Label>
              <Input
                id="sede-nombre"
                value={form.nombre}
                onChange={(event) => setForm({ ...form, nombre: event.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sede-ciudad">Ciudad</Label>
              <Input
                id="sede-ciudad"
                value={form.ciudad}
                onChange={(event) => setForm({ ...form, ciudad: event.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sede-codigo">Código (1 carácter)</Label>
              <Input
                id="sede-codigo"
                value={form.codigo}
                onChange={(event) => setForm({ ...form, codigo: event.target.value.toUpperCase() })}
                maxLength={1}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sede-imagen">Imagen (URL)</Label>
              <Input
                id="sede-imagen"
                value={form.image_url}
                onChange={(event) => setForm({ ...form, image_url: event.target.value })}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="sede-descripcion">Descripción</Label>
              <Input
                id="sede-descripcion"
                value={form.descripcion}
                onChange={(event) => setForm({ ...form, descripcion: event.target.value })}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="sede-maps">Google Maps (URL)</Label>
              <Input
                id="sede-maps"
                value={form.maps_url}
                onChange={(event) => setForm({ ...form, maps_url: event.target.value })}
              />
            </div>
            <label className="flex items-center gap-2 text-sm md:col-span-2">
              <input
                type="checkbox"
                className="h-4 w-4 accent-[#A92730]"
                checked={form.activo}
                onChange={(event) => setForm({ ...form, activo: event.target.checked })}
              />
              <span className="text-ink/70">Sede activa</span>
            </label>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={!form.nombre || !form.codigo || mutation.isPending}>
              {mutation.isPending ? "Guardando..." : form.id ? "Guardar cambios" : "Crear sede"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
