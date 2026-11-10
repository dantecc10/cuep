"use client";
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export function useConfirmDialog() {
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState({ title: "Confirmar", description: "¿Deseas continuar?", confirmText: "Confirmar", cancelText: "Cancelar" });
  const [resolver, setResolver] = useState<((value: boolean) => void) | null>(null);

  const confirm = (next: Partial<typeof options>) => {
    setOptions((prev) => ({ ...prev, ...next }));
    setOpen(true);
    return new Promise<boolean>((resolve) => setResolver(() => resolve));
  };

  const close = (value: boolean) => {
    setOpen(false);
    resolver?.(value);
    setResolver(null);
  };

  const dialog = (
    <Dialog open={open} onOpenChange={(value) => !value && close(false)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{options.title}</DialogTitle>
          <DialogDescription>{options.description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => close(false)}>{options.cancelText}</Button>
          <Button onClick={() => close(true)}>{options.confirmText}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  return { confirm, dialog };
}
