"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Banknote, Download, QrCode, Search, UserCheck } from "lucide-react";
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

interface Page {
  items: Aspirante[];
  total: number;
}

interface Aspirante {
  id: number;
  matricula: string | null;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  estatus: string;
  checkin_at: string | null;
  sede_id: number | null;
}

interface Cargo {
  id: number;
  concepto: string;
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
  recibo_codigo: string | null;
}

interface Detalle extends Aspirante {
  cargos: Cargo[];
  pagos: Pago[];
  saldo: number;
}

function money(value: number, currency = "MXN") {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency }).format(value);
}

function formatDate(value: string | null) {
  if (!value) return "Pendiente";
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export default function InscripcionPresencialPage() {
  const token = useAuthStore((s) => s.token);
  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);
  const [identifier, setIdentifier] = useState("");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [cash, setCash] = useState({ cargo_id: 0, monto: "" });

  const { data: results, isLoading } = useQuery<Page>({
    queryKey: ["presencial-search", search],
    queryFn: async () =>
      (
        await api.get("/inscripciones", {
          headers,
          params: { search, page_size: 10 },
        })
      ).data,
    enabled: Boolean(token && search),
  });

  const { data: detalle, refetch: refetchDetalle, isLoading: detailLoading } = useQuery<Detalle>({
    queryKey: ["presencial-detalle", selectedId],
    queryFn: async () => (await api.get(`/inscripciones/${selectedId}`, { headers })).data,
    enabled: Boolean(token && selectedId),
  });

  const openCargos = (detalle?.cargos || []).filter(
    (cargo) => cargo.estado === "pendiente" || cargo.estado === "parcial",
  );

  const paidByCargo = useMemo(() => {
    const totals = new Map<number, number>();
    for (const pago of detalle?.pagos || []) {
      if (pago.estado !== "validado") continue;
      totals.set(pago.cargo_id, (totals.get(pago.cargo_id) || 0) + Number(pago.monto));
    }
    return totals;
  }, [detalle?.pagos]);

  function selectStudent(student: Aspirante) {
    setSelectedId(student.id);
    setCash({ cargo_id: 0, monto: "" });
  }

  function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    setSelectedId(null);
    setSearch(identifier.trim());
  }

  async function confirmCheckin() {
    if (!detalle) return;
    setBusy(true);
    try {
      const response = await api.post(
        "/inscripciones/checkin",
        { identificador: detalle.matricula || String(detalle.id) },
        { headers },
      );
      toast.success(
        response.data.ya_registrado
          ? "Este pase ya tenía check-in."
          : "Check-in registrado correctamente.",
      );
      await refetchDetalle();
    } catch {
      toast.error("No pudimos registrar el check-in.");
    } finally {
      setBusy(false);
    }
  }

  async function registerCash(event: React.FormEvent) {
    event.preventDefault();
    if (!cash.cargo_id || !cash.monto) {
      toast.error("Selecciona un cargo y escribe el monto.");
      return;
    }
    setBusy(true);
    try {
      const response = await api.post(
        "/pagos",
        { cargo_id: cash.cargo_id, monto: Number(cash.monto), metodo: "efectivo" },
        { headers },
      );
      toast.success(`Pago registrado. Recibo: ${response.data.recibo_codigo || "generado"}`);
      setCash({ cargo_id: 0, monto: "" });
      await refetchDetalle();
    } catch {
      toast.error("No pudimos registrar el pago en efectivo.");
    } finally {
      setBusy(false);
    }
  }

  async function downloadRecibo(pagoId: number) {
    try {
      const response = await api.get(`/pagos/${pagoId}/recibo`, {
        headers,
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `recibo-${pagoId}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("No pudimos descargar el recibo.");
    }
  }

  return (
    <AppShell title="Inscripción presencial">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Módulo de sede"
          title="Inscripción presencial"
          description="Escanea el pase, confirma la asistencia y registra pagos en efectivo. Transferencias se validan en el módulo de pagos."
        />

        <div className="poster-card p-5">
          <p className="type-kicker flex items-center gap-2">
            <QrCode className="h-4 w-4" /> Buscar pase
          </p>
          <form onSubmit={handleSearch} className="mt-3 flex flex-col gap-2 sm:flex-row">
            <label className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/40" />
              <Input
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                placeholder="Escanea el QR o escribe matrícula, correo o teléfono"
                className="h-11 w-full pl-9"
                autoFocus
              />
            </label>
            <Button type="submit" className="h-11">Buscar</Button>
          </form>
          <p className="mt-2 text-xs text-ink/45">
            El lector QR funciona como teclado: coloca el cursor aquí y escanea el pase.
          </p>
        </div>

        {isLoading ? (
          <div className="h-24 animate-pulse bg-ink/10" />
        ) : search && results && results.items.length > 1 ? (
          <Card>
            <CardHeader><CardTitle>Coincidencias</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {results.items.map((student) => (
                <button
                  key={student.id}
                  type="button"
                  onClick={() => selectStudent(student)}
                  className={`flex w-full items-center justify-between gap-3 border p-3 text-left transition ${
                    selectedId === student.id ? "border-primary bg-primary/5" : "border-ink/15 hover:border-ink/40"
                  }`}
                >
                  <span>
                    <span className="block font-semibold text-ink">{student.full_name}</span>
                    <span className="block font-mono text-xs text-ink/50">{student.matricula}</span>
                  </span>
                  <StatusBadge status={student.estatus} />
                </button>
              ))}
            </CardContent>
          </Card>
        ) : null}

        {search && results && results.items.length === 0 && !isLoading ? (
          <div className="border border-dashed border-ink/25 bg-surface px-4 py-10 text-center">
            <p className="font-editorial text-base text-ink/55">
              No encontramos una inscripción con ese dato.
            </p>
          </div>
        ) : null}

        {selectedId ? (
          <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between gap-3">
                  <span>Pase seleccionado</span>
                  {detalle ? <StatusBadge status={detalle.estatus} /> : null}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {detailLoading || !detalle ? (
                  <div className="h-48 animate-pulse bg-ink/10" />
                ) : (
                  <>
                    <div>
                      <p className="font-display text-3xl uppercase leading-none text-ink">
                        {detalle.full_name}
                      </p>
                      <p className="mt-1 font-mono text-sm font-bold text-primary">{detalle.matricula}</p>
                      <p className="mt-1 text-xs text-ink/50">{detalle.email || "Sin correo"}</p>
                    </div>
                    <dl className="grid gap-2 text-sm sm:grid-cols-2">
                      <div>
                        <dt className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/45">Teléfono</dt>
                        <dd className="text-ink/75">{detalle.phone || "—"}</dd>
                      </div>
                      <div>
                        <dt className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/45">Check-in</dt>
                        <dd className={detalle.checkin_at ? "font-semibold text-ink" : "text-ink/60"}>
                          {formatDate(detalle.checkin_at)}
                        </dd>
                      </div>
                    </dl>
                    <Button className="w-full" onClick={confirmCheckin} disabled={busy || Boolean(detalle.checkin_at)}>
                      <UserCheck className="mr-2 h-4 w-4" />
                      {detalle.checkin_at ? "Check-in ya registrado" : "Confirmar check-in"}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Banknote className="h-4 w-4" /> Cobro en efectivo
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {!detalle ? (
                  <div className="h-40 animate-pulse bg-ink/10" />
                ) : openCargos.length === 0 ? (
                  <p className="text-sm text-ink/55">No hay cargos pendientes para este aspirante.</p>
                ) : (
                  <form onSubmit={registerCash} className="space-y-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="cargo">Cargo</Label>
                      <select
                        id="cargo"
                        className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                        value={cash.cargo_id || ""}
                        onChange={(event) => {
                          const cargoId = Number(event.target.value);
                          const cargo = openCargos.find((item) => item.id === cargoId);
                          const paid = paidByCargo.get(cargoId) || 0;
                          setCash({
                            cargo_id: cargoId,
                            monto: cargo ? String(Math.max(Number(cargo.monto) - paid, 0)) : "",
                          });
                        }}
                        required
                      >
                        <option value="" disabled>Selecciona un cargo</option>
                        {openCargos.map((cargo) => {
                          const paid = paidByCargo.get(cargo.id) || 0;
                          const remaining = Math.max(Number(cargo.monto) - paid, 0);
                          return (
                            <option key={cargo.id} value={cargo.id}>
                              {cargo.concepto} · restante {money(remaining, cargo.moneda)}
                            </option>
                          );
                        })}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="monto">Monto recibido</Label>
                      <Input
                        id="monto"
                        type="number"
                        min="0.01"
                        step="0.01"
                        className="h-10"
                        value={cash.monto}
                        onChange={(event) => setCash({ ...cash, monto: event.target.value })}
                        required
                      />
                    </div>
                    <Button type="submit" className="w-full" disabled={busy}>
                      Registrar pago y generar recibo
                    </Button>
                  </form>
                )}

                <div>
                  <p className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.08em] text-ink/50">
                    Pagos registrados
                  </p>
                  {(detalle?.pagos || []).length === 0 ? (
                    <p className="mt-1 text-xs text-ink/50">Sin pagos.</p>
                  ) : (
                    detalle?.pagos.map((pago) => (
                      <div key={pago.id} className="mt-2 flex items-center justify-between gap-2 border-t border-ink/10 pt-2 text-xs">
                        <span className="capitalize">
                          {pago.metodo} · {money(pago.monto, pago.moneda)}
                        </span>
                        <div className="flex items-center gap-1">
                          <StatusBadge status={pago.estado} />
                          {pago.estado === "validado" ? (
                            <Button size="sm" variant="ghost" onClick={() => downloadRecibo(pago.id)}>
                              <Download className="h-3.5 w-3.5" />
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        ) : search && results?.items.length === 1 ? (
          <div className="poster-card flex flex-wrap items-center justify-between gap-3 p-4">
            <p className="text-sm text-ink/65">
              Encontramos a <strong className="text-ink">{results.items[0].full_name}</strong>.
            </p>
            <Button size="sm" onClick={() => selectStudent(results.items[0])}>Abrir pase</Button>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
