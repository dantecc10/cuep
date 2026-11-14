"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Banknote, Download, ReceiptText, Upload } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Cargo {
  id: number;
  anio: number;
  concepto: string;
  descripcion: string | null;
  monto: number;
  moneda: string;
  estado: string;
}

interface Pago {
  id: number;
  cargo_id: number;
  monto: number;
  moneda: string;
  metodo: string;
  estado: string;
  referencia: string | null;
  comprobante_nombre: string | null;
  recibo_codigo: string | null;
  motivo_rechazo: string | null;
  created_at: string;
}

interface Inscripcion {
  cargos: Cargo[];
  pagos: Pago[];
  saldo: number;
}

interface Config {
  anio: number;
  simulacro_activo: boolean;
  simulacro_monto: number;
  simulacro_moneda: string;
  pago_efectivo_habilitado: boolean;
  transferencia_habilitada: boolean;
  transferencia_banco: string | null;
  transferencia_titular: string | null;
  transferencia_clabe: string | null;
  transferencia_instrucciones: string | null;
}

function money(value: number, currency = "MXN") {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency }).format(value);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export default function MiPagosPage() {
  const token = useAuthStore((s) => s.token);
  const [data, setData] = useState<Inscripcion | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [transfer, setTransfer] = useState({ cargo_id: 0, monto: "", referencia: "", file: null as File | null });

  const headers = useMemo(
    () => (token ? { Authorization: `Bearer ${token}` } : {}),
    [token],
  );

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [inscripcion, configuracion] = await Promise.all([
        api.get<Inscripcion>("/inscripciones/me", { headers }),
        api.get<Config>("/inscripciones/config"),
      ]);
      setData(inscripcion.data);
      setConfig(configuracion.data);
      const firstOpen = inscripcion.data.cargos.find(
        (cargo) => cargo.estado === "pendiente" || cargo.estado === "parcial",
      );
      if (firstOpen) {
        setTransfer((current) => ({
          ...current,
          cargo_id: current.cargo_id || firstOpen.id,
          monto: current.monto || String(firstOpen.monto),
        }));
      }
    } catch {
      setError("No pudimos cargar tus pagos. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  }, [headers, token]);

  useEffect(() => {
    void load();
  }, [load]);

  const paidByCargo = useMemo(() => {
    const totals = new Map<number, number>();
    for (const pago of data?.pagos || []) {
      if (pago.estado !== "validado") continue;
      totals.set(pago.cargo_id, (totals.get(pago.cargo_id) || 0) + Number(pago.monto));
    }
    return totals;
  }, [data?.pagos]);

  async function requestSimulacro() {
    setBusy(true);
    try {
      const response = await api.post("/pagos/simulacro", {}, { headers });
      toast.success(
        response.data.creado
          ? "Tu lugar para el simulacro quedó registrado."
          : "Ya tenías registrado el simulacro.",
      );
      await load();
    } catch {
      toast.error("No pudimos registrar el simulacro.");
    } finally {
      setBusy(false);
    }
  }

  async function submitTransfer(event: React.FormEvent) {
    event.preventDefault();
    if (!transfer.cargo_id || !transfer.monto || !transfer.file) {
      toast.error("Selecciona el cargo, el monto y adjunta tu comprobante.");
      return;
    }
    setBusy(true);
    try {
      const pagoResponse = await api.post(
        "/pagos",
        {
          cargo_id: transfer.cargo_id,
          monto: Number(transfer.monto),
          metodo: "transferencia",
          referencia: transfer.referencia || undefined,
        },
        { headers },
      );
      const formData = new FormData();
      formData.append("file", transfer.file);
      await api.post(`/pagos/${pagoResponse.data.id}/comprobante`, formData, {
        headers: { ...headers, "Content-Type": "multipart/form-data" },
      });
      toast.success("Recibimos tu comprobante. El equipo lo revisará.");
      setTransfer({ cargo_id: 0, monto: "", referencia: "", file: null });
      await load();
    } catch {
      toast.error("No pudimos registrar tu transferencia. Revisa el monto y el archivo.");
    } finally {
      setBusy(false);
    }
  }

  async function downloadRecibo(pago: Pago) {
    try {
      const response = await api.get(`/pagos/${pago.id}/recibo`, {
        headers,
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `recibo-${pago.recibo_codigo || pago.id}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("El recibo aún no está disponible.");
    }
  }

  const openCargos = (data?.cargos || []).filter(
    (cargo) => cargo.estado === "pendiente" || cargo.estado === "parcial",
  );
  const hasSimulacro = (data?.cargos || []).some((cargo) => cargo.concepto === "simulacro");

  return (
    <AppShell title="Mis pagos">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Simulacro de admisión"
          title="Mis pagos"
          description="Consulta tus cargos, sube tu comprobante de transferencia y descarga tus recibos."
          actions={
            config?.simulacro_activo && !hasSimulacro ? (
              <Button onClick={requestSimulacro} disabled={busy}>
                <ReceiptText className="mr-2 h-4 w-4" />
                Solicitar simulacro
              </Button>
            ) : undefined
          }
        />

        {error ? (
          <div className="poster-card flex flex-wrap items-center justify-between gap-3 p-4">
            <p className="text-sm font-semibold text-primary">{error}</p>
            <Button variant="outline" size="sm" onClick={load}>
              Reintentar
            </Button>
          </div>
        ) : null}

        {loading ? (
          <div className="poster-card p-8">
            <div className="h-5 w-52 animate-pulse bg-ink/10" />
            <div className="mt-4 h-32 animate-pulse bg-ink/10" />
          </div>
        ) : (
          <section className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
            <div className="space-y-5">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between gap-3">
                    <span className="flex items-center gap-2">
                      <Banknote className="h-4 w-4" /> Cargos
                    </span>
                    <span className="font-mono text-xs text-ink/50">
                      Saldo {money(data?.saldo || 0)}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(data?.cargos || []).length === 0 ? (
                    <p className="text-sm text-ink/55">
                      No tienes cargos. El simulacro es opcional y no bloquea tu inscripción.
                    </p>
                  ) : (
                    data?.cargos.map((cargo) => {
                      const paid = paidByCargo.get(cargo.id) || 0;
                      const remaining = Math.max(Number(cargo.monto) - paid, 0);
                      return (
                        <div key={cargo.id} className="border border-ink/15 bg-sand/40 p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <p className="font-display text-xl uppercase text-ink">
                                {cargo.concepto}
                              </p>
                              <p className="text-xs text-ink/55">
                                {cargo.descripcion || "Cargo del proceso"} · {cargo.anio}
                              </p>
                            </div>
                            <StatusBadge status={cargo.estado} />
                          </div>
                          <div className="mt-3 flex flex-wrap gap-4 text-sm">
                            <span>Total: {money(cargo.monto, cargo.moneda)}</span>
                            <span>Pagado: {money(paid, cargo.moneda)}</span>
                            <span className="font-semibold text-primary">
                              Restante: {money(remaining, cargo.moneda)}
                            </span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ReceiptText className="h-4 w-4" /> Historial de pagos
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {(data?.pagos || []).length === 0 ? (
                    <p className="text-sm text-ink/55">Todavía no registras pagos.</p>
                  ) : (
                    data?.pagos.map((pago) => (
                      <div
                        key={pago.id}
                        className="flex flex-wrap items-center justify-between gap-3 border border-ink/15 p-3"
                      >
                        <div>
                          <p className="font-semibold capitalize text-ink">
                            {pago.metodo} · {money(pago.monto, pago.moneda)}
                          </p>
                          <p className="text-xs text-ink/50">
                            {formatDate(pago.created_at)}
                            {pago.recibo_codigo ? ` · ${pago.recibo_codigo}` : ""}
                          </p>
                          {pago.motivo_rechazo ? (
                            <p className="mt-1 text-xs font-semibold text-primary">
                              {pago.motivo_rechazo}
                            </p>
                          ) : null}
                        </div>
                        <div className="flex items-center gap-2">
                          <StatusBadge status={pago.estado} />
                          {pago.estado === "validado" ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => downloadRecibo(pago)}
                            >
                              <Download className="mr-1 h-3.5 w-3.5" /> Recibo
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-5">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-4 w-4" /> Transferencia
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {config?.transferencia_habilitada ? (
                    <>
                      <div className="border border-ink/15 bg-sand/50 p-4 text-sm">
                        <p className="font-semibold text-ink">
                          {config.transferencia_banco || "Datos bancarios"}
                        </p>
                        <p className="mt-1 text-ink/70">
                          Titular: {config.transferencia_titular || "Por confirmar"}
                        </p>
                        <p className="text-ink/70">CLABE: {config.transferencia_clabe || "Por confirmar"}</p>
                        {config.transferencia_instrucciones ? (
                          <p className="mt-2 text-xs leading-relaxed text-ink/55">
                            {config.transferencia_instrucciones}
                          </p>
                        ) : null}
                      </div>
                      <form onSubmit={submitTransfer} className="space-y-3">
                        <div className="space-y-1.5">
                          <Label htmlFor="cargo">Cargo</Label>
                          <select
                            id="cargo"
                            className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                            value={transfer.cargo_id}
                            onChange={(event) =>
                              setTransfer({ ...transfer, cargo_id: Number(event.target.value) })
                            }
                            required
                          >
                            <option value={0} disabled>
                              Selecciona un cargo
                            </option>
                            {openCargos.map((cargo) => (
                              <option key={cargo.id} value={cargo.id}>
                                {cargo.concepto} · {money(cargo.monto, cargo.moneda)}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="monto">Monto transferido</Label>
                          <Input
                            id="monto"
                            type="number"
                            min="0.01"
                            step="0.01"
                            value={transfer.monto}
                            onChange={(event) => setTransfer({ ...transfer, monto: event.target.value })}
                            required
                          />
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="referencia">Referencia</Label>
                          <Input
                            id="referencia"
                            value={transfer.referencia}
                            onChange={(event) =>
                              setTransfer({ ...transfer, referencia: event.target.value })
                            }
                            placeholder="Folio o referencia bancaria"
                          />
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="comprobante">Comprobante</Label>
                          <Input
                            id="comprobante"
                            type="file"
                            accept="application/pdf,image/jpeg,image/png,image/webp"
                            onChange={(event) =>
                              setTransfer({ ...transfer, file: event.target.files?.[0] || null })
                            }
                            required
                          />
                          <p className="text-xs text-ink/45">PDF, JPG, PNG o WEBP. Máximo 10 MB.</p>
                        </div>
                        <Button type="submit" className="w-full" disabled={busy || openCargos.length === 0}>
                          {busy ? "Enviando..." : "Subir comprobante"}
                        </Button>
                      </form>
                    </>
                  ) : (
                    <p className="text-sm leading-relaxed text-ink/60">
                      La transferencia todavía no está habilitada. Puedes pagar en efectivo
                      directamente en tu sede durante la inscripción presencial.
                    </p>
                  )}
                </CardContent>
              </Card>

              <div className="poster-card p-5">
                <p className="type-kicker">Recuerda</p>
                <p className="mt-3 font-editorial text-xl font-semibold leading-tight text-ink">
                  El simulacro es opcional y no bloquea tu inscripción.
                </p>
                <p className="mt-2 text-sm leading-relaxed text-ink/60">
                  Si decides participar, conserva tu comprobante y revisa que el monto coincida
                  con el cargo. El personal valida cada transferencia manualmente.
                </p>
              </div>
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
