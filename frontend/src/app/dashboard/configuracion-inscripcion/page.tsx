"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Save, Settings } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Config {
  anio: number;
  registro_abierto: boolean;
  simulacro_activo: boolean;
  simulacro_monto: number;
  simulacro_moneda: string;
  pago_efectivo_habilitado: boolean;
  transferencia_habilitada: boolean;
  transferencia_banco: string | null;
  transferencia_titular: string | null;
  transferencia_clabe: string | null;
  transferencia_instrucciones: string | null;
  parcialidades_permitidas: boolean;
  parcialidades_max: number;
  donativo_obligatorio: boolean;
  donativo_descripcion: string | null;
}

const defaults: Config = {
  anio: new Date().getFullYear(),
  registro_abierto: true,
  simulacro_activo: false,
  simulacro_monto: 0,
  simulacro_moneda: "MXN",
  pago_efectivo_habilitado: true,
  transferencia_habilitada: false,
  transferencia_banco: "",
  transferencia_titular: "",
  transferencia_clabe: "",
  transferencia_instrucciones: "",
  parcialidades_permitidas: false,
  parcialidades_max: 1,
  donativo_obligatorio: false,
  donativo_descripcion: "",
};

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-start justify-between gap-4 border border-ink/15 bg-sand/35 p-4">
      <span>
        <span className="block text-sm font-semibold text-ink">{label}</span>
        <span className="mt-1 block text-xs leading-relaxed text-ink/55">{description}</span>
      </span>
      <input
        type="checkbox"
        className="mt-1 h-5 w-5 shrink-0 accent-[#A92730]"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  );
}

export default function ConfiguracionInscripcionPage() {
  const token = useAuthStore((s) => s.token);
  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);
  const [form, setForm] = useState<Config>(defaults);
  const [busy, setBusy] = useState(false);

  const { data, isLoading } = useQuery<Config>({
    queryKey: ["inscripcion-config-admin"],
    queryFn: async () => (await api.get("/inscripciones/config", { headers })).data,
    enabled: Boolean(token),
  });

  useEffect(() => {
    if (!data) return;
    setForm({
      ...defaults,
      ...data,
      transferencia_banco: data.transferencia_banco || "",
      transferencia_titular: data.transferencia_titular || "",
      transferencia_clabe: data.transferencia_clabe || "",
      transferencia_instrucciones: data.transferencia_instrucciones || "",
      donativo_descripcion: data.donativo_descripcion || "",
    });
  }, [data]);

  function update<K extends keyof Config>(key: K, value: Config[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const response = await api.put(
        "/inscripciones/config",
        {
          ...form,
          transferencia_banco: form.transferencia_banco || null,
          transferencia_titular: form.transferencia_titular || null,
          transferencia_clabe: form.transferencia_clabe || null,
          transferencia_instrucciones: form.transferencia_instrucciones || null,
          donativo_descripcion: form.donativo_descripcion || null,
        },
        { headers },
      );
      setForm((current) => ({ ...current, ...response.data }));
      toast.success("Configuración guardada.");
    } catch {
      toast.error("No pudimos guardar la configuración.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Configuración de inscripción">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Cierre y apertura anual"
          title="Configuración"
          description="Define el año activo, el registro, el simulacro y los datos de pago que verán las y los aspirantes."
        />

        {isLoading ? (
          <div className="h-64 animate-pulse bg-ink/10" />
        ) : (
          <form onSubmit={save} className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-4 w-4" /> Ciclo y registro
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="anio">Año activo</Label>
                  <Input
                    id="anio"
                    type="number"
                    min="2000"
                    max="2100"
                    className="h-10"
                    value={form.anio}
                    onChange={(event) => update("anio", Number(event.target.value))}
                    required
                  />
                  <p className="text-xs text-ink/45">
                    Las nuevas inscripciones se etiquetan con este año.
                  </p>
                </div>
                <Toggle
                  label="Registro abierto"
                  description="Permite que nuevas personas creen su cuenta y generen matrícula."
                  checked={form.registro_abierto}
                  onChange={(value) => update("registro_abierto", value)}
                />
                <Toggle
                  label="Pago en efectivo habilitado"
                  description="Permite al personal de sede registrar cobros en efectivo."
                  checked={form.pago_efectivo_habilitado}
                  onChange={(value) => update("pago_efectivo_habilitado", value)}
                />
                <Toggle
                  label="Parcialidades permitidas"
                  description="Permite registrar abonos parciales sobre un cargo."
                  checked={form.parcialidades_permitidas}
                  onChange={(value) => update("parcialidades_permitidas", value)}
                />
                <div className="space-y-1.5">
                  <Label htmlFor="parcialidades_max">Máximo de parcialidades</Label>
                  <Input
                    id="parcialidades_max"
                    type="number"
                    min="1"
                    className="h-10"
                    value={form.parcialidades_max}
                    onChange={(event) => update("parcialidades_max", Number(event.target.value))}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Simulacro</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Toggle
                  label="Simulacro activo"
                  description="Muestra la opción de participar. Es opt-in y no bloquea la inscripción."
                  checked={form.simulacro_activo}
                  onChange={(value) => update("simulacro_activo", value)}
                />
                <div className="grid gap-4 sm:grid-cols-[1fr_120px]">
                  <div className="space-y-1.5">
                    <Label htmlFor="simulacro_monto">Costo del simulacro</Label>
                    <Input
                      id="simulacro_monto"
                      type="number"
                      min="0"
                      step="0.01"
                      className="h-10"
                      value={form.simulacro_monto}
                      onChange={(event) => update("simulacro_monto", Number(event.target.value))}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="simulacro_moneda">Moneda</Label>
                    <Input
                      id="simulacro_moneda"
                      className="h-10"
                      value={form.simulacro_moneda}
                      onChange={(event) => update("simulacro_moneda", event.target.value.toUpperCase())}
                      maxLength={10}
                    />
                  </div>
                </div>
                <Toggle
                  label="Donativo obligatorio"
                  description="Si se activa, el donativo se presenta como requisito del proceso."
                  checked={form.donativo_obligatorio}
                  onChange={(value) => update("donativo_obligatorio", value)}
                />
                <div className="space-y-1.5">
                  <Label htmlFor="donativo_descripcion">Descripción del donativo</Label>
                  <textarea
                    id="donativo_descripcion"
                    rows={3}
                    className="w-full border border-ink/30 bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:border-primary"
                    value={form.donativo_descripcion || ""}
                    onChange={(event) => update("donativo_descripcion", event.target.value)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Transferencias</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Toggle
                  label="Transferencia habilitada"
                  description="Muestra los datos bancarios a las y los aspirantes. Requiere almacenamiento privado para comprobantes."
                  checked={form.transferencia_habilitada}
                  onChange={(value) => update("transferencia_habilitada", value)}
                />
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="transferencia_banco">Banco</Label>
                    <Input
                      id="transferencia_banco"
                      className="h-10"
                      value={form.transferencia_banco || ""}
                      onChange={(event) => update("transferencia_banco", event.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="transferencia_titular">Titular</Label>
                    <Input
                      id="transferencia_titular"
                      className="h-10"
                      value={form.transferencia_titular || ""}
                      onChange={(event) => update("transferencia_titular", event.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label htmlFor="transferencia_clabe">CLABE</Label>
                    <Input
                      id="transferencia_clabe"
                      className="h-10 font-mono"
                      value={form.transferencia_clabe || ""}
                      onChange={(event) => update("transferencia_clabe", event.target.value)}
                      maxLength={20}
                    />
                  </div>
                  <div className="space-y-1.5 sm:col-span-2">
                    <Label htmlFor="transferencia_instrucciones">Instrucciones</Label>
                    <textarea
                      id="transferencia_instrucciones"
                      rows={3}
                      className="w-full border border-ink/30 bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:border-primary"
                      value={form.transferencia_instrucciones || ""}
                      onChange={(event) => update("transferencia_instrucciones", event.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end lg:col-span-2">
              <Button type="submit" disabled={busy}>
                <Save className="mr-2 h-4 w-4" /> {busy ? "Guardando..." : "Guardar configuración"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </AppShell>
  );
}
