"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import QRCode from "react-qr-code";
import { CalendarCheck, Download, FileText, Wallet } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Sede {
  id: number;
  nombre: string;
  ciudad: string | null;
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
  monto: number;
  moneda: string;
  metodo: string;
  estado: string;
  recibo_codigo: string | null;
  created_at: string;
}

interface Evento {
  id: number;
  tipo: string;
  estado_nuevo: string | null;
  created_at: string;
}

interface Inscripcion {
  id: number;
  matricula: string | null;
  folio: number | null;
  estatus: string;
  anio: number;
  nivel: string;
  area: string | null;
  sede_id: number | null;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  qr_token: string | null;
  checkin_at: string | null;
  pase_url: string | null;
  cargos: Cargo[];
  pagos: Pago[];
  eventos: Evento[];
  saldo: number;
}

const statusCopy: Record<string, string> = {
  registrado: "Tu registro está listo. Ahora toca la inscripción presencial.",
  en_inscripcion: "Estás en el proceso de inscripción presencial.",
  inscrito: "Tu inscripción quedó completa.",
  activo: "Tu inscripción está activa.",
  no_asistio: "No registramos tu asistencia. Contacta a tu sede.",
  cancelado: "Tu inscripción fue cancelada.",
  baja: "Tu inscripción está de baja.",
};

function formatDate(value: string | null) {
  if (!value) return "Pendiente";
  return new Intl.DateTimeFormat("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function money(value: number, currency = "MXN") {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency }).format(value);
}

export default function MiRegistroPage() {
  const token = useAuthStore((s) => s.token);
  const [data, setData] = useState<Inscripcion | null>(null);
  const [sedes, setSedes] = useState<Sede[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [inscripcion, sedesResponse] = await Promise.all([
        api.get<Inscripcion>("/inscripciones/me", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        api.get<Sede[]>("/sedes"),
      ]);
      setData(inscripcion.data);
      setSedes(sedesResponse.data);
    } catch {
      setError("No pudimos cargar tu registro. Si aún no te registras, crea tu cuenta primero.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const sede = useMemo(
    () => sedes.find((item) => item.id === data?.sede_id),
    [sedes, data?.sede_id],
  );

  async function downloadPase() {
    if (!token || !data) return;
    setDownloading(true);
    try {
      const response = await api.get("/inscripciones/me/pase", {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `pase-${data.matricula || data.id}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("No pudimos descargar tu pase. Intenta de nuevo.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <AppShell title="Mi registro">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Proceso de inscripción"
          title="Mi registro"
          description="Tu matrícula, tu pase y el estado de tu proceso en un solo lugar."
          actions={
            data ? (
              <Button variant="outline" onClick={downloadPase} disabled={downloading}>
                <Download className="mr-2 h-4 w-4" />
                {downloading ? "Generando..." : "Descargar pase"}
              </Button>
            ) : undefined
          }
        />

        {loading ? (
          <div className="poster-card p-8">
            <div className="h-5 w-40 animate-pulse bg-ink/10" />
            <div className="mt-4 h-24 animate-pulse bg-ink/10" />
          </div>
        ) : error ? (
          <div className="poster-card space-y-4 p-6">
            <p className="text-sm font-semibold text-primary">{error}</p>
            <div className="flex flex-wrap gap-3">
              <Link href="/registro">
                <Button>Crear mi registro</Button>
              </Link>
              <Button variant="outline" onClick={load}>
                Reintentar
              </Button>
            </div>
          </div>
        ) : data ? (
          <>
            <section className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="poster-card overflow-hidden">
                <div className="border-b border-dashed border-ink/25 bg-accent/15 px-6 py-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="type-kicker text-ink/60">Pase de inscripción · {data.anio}</p>
                      <h2 className="mt-2 font-display text-4xl uppercase leading-none text-primary">
                        {data.full_name || "Aspirante CUEP"}
                      </h2>
                    </div>
                    <StatusBadge status={data.estatus} />
                  </div>
                </div>
                <div className="grid gap-6 p-6 sm:grid-cols-[1fr_auto] sm:items-center">
                  <div className="space-y-4">
                    <div>
                      <p className="type-label text-ink/45">Matrícula</p>
                      <p className="font-mono text-3xl font-bold tracking-[0.12em] text-ink">
                        {data.matricula || "Pendiente"}
                      </p>
                    </div>
                    <dl className="grid gap-3 text-sm sm:grid-cols-2">
                      <div>
                        <dt className="type-label text-ink/45">Sede</dt>
                        <dd className="mt-1 font-semibold text-ink">{sede?.nombre || "Por confirmar"}</dd>
                      </div>
                      <div>
                        <dt className="type-label text-ink/45">Nivel</dt>
                        <dd className="mt-1 font-semibold text-ink">{data.nivel}</dd>
                      </div>
                      <div>
                        <dt className="type-label text-ink/45">Área</dt>
                        <dd className="mt-1 font-semibold text-ink">{data.area || "Por definir"}</dd>
                      </div>
                      <div>
                        <dt className="type-label text-ink/45">Asistencia</dt>
                        <dd className="mt-1 font-semibold text-ink">{formatDate(data.checkin_at)}</dd>
                      </div>
                    </dl>
                  </div>
                  <div className="mx-auto border-[1.5px] border-ink bg-white p-3 shadow-[5px_5px_0_#A92730]">
                    {data.pase_url ? (
                      <QRCode value={data.pase_url} size={164} />
                    ) : (
                      <div className="grid h-[164px] w-[164px] place-items-center text-center text-xs text-ink/45">
                        QR en preparación
                      </div>
                    )}
                    <p className="mt-2 text-center font-mono text-[0.55rem] uppercase tracking-[0.12em] text-ink/50">
                      Presenta este código
                    </p>
                  </div>
                </div>
                <div className="border-t border-ink/10 bg-sand/50 px-6 py-4">
                  <p className="text-sm leading-relaxed text-ink/70">
                    {statusCopy[data.estatus] || "Revisa tu estado con el equipo de tu sede."}
                  </p>
                </div>
              </div>

              <div className="space-y-5">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Wallet className="h-4 w-4" /> Simulacro y pagos
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-end justify-between border-b border-ink/10 pb-3">
                      <span className="text-sm text-ink/60">Saldo pendiente</span>
                      <span className="font-display text-3xl uppercase text-primary">
                        {money(data.saldo)}
                      </span>
                    </div>
                    {data.cargos.length === 0 ? (
                      <p className="text-sm text-ink/55">
                        Aún no tienes cargos. Puedes solicitar el simulacro desde Mis pagos.
                      </p>
                    ) : (
                      data.cargos.map((cargo) => (
                        <div key={cargo.id} className="flex items-center justify-between gap-3 text-sm">
                          <div>
                            <p className="font-semibold capitalize text-ink">{cargo.concepto}</p>
                            <p className="text-xs text-ink/50">{money(cargo.monto, cargo.moneda)}</p>
                          </div>
                          <StatusBadge status={cargo.estado} />
                        </div>
                      ))
                    )}
                    {data.pagos.slice(0, 3).map((pago) => (
                      <div key={pago.id} className="flex items-center justify-between gap-3 border-t border-ink/10 pt-3 text-sm">
                        <div>
                          <p className="font-semibold text-ink">Pago {pago.metodo}</p>
                          <p className="text-xs text-ink/50">
                            {money(pago.monto, pago.moneda)} · {formatDate(pago.created_at)}
                          </p>
                        </div>
                        <StatusBadge status={pago.estado} />
                      </div>
                    ))}
                    <Link href="/mi-pagos" className="block">
                      <Button className="w-full" variant="outline">
                        Ir a Mis pagos
                      </Button>
                    </Link>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CalendarCheck className="h-4 w-4" /> Actividad reciente
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {data.eventos.length === 0 ? (
                      <p className="text-sm text-ink/55">Todavía no hay movimientos.</p>
                    ) : (
                      data.eventos.slice(0, 6).map((evento) => (
                        <div key={evento.id} className="flex gap-3 border-l-2 border-accent pl-3">
                          <div>
                            <p className="text-sm font-semibold capitalize text-ink">
                              {evento.tipo.replaceAll("_", " ")}
                            </p>
                            <p className="text-xs text-ink/50">{formatDate(evento.created_at)}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </CardContent>
                </Card>
              </div>
            </section>

            <section className="grid gap-4 sm:grid-cols-3">
              {[
                {
                  icon: FileText,
                  title: "1. Registro",
                  body: "Crea tu cuenta y recibe tu matrícula y pase.",
                },
                {
                  icon: Download,
                  title: "2. Pase",
                  body: "Descarga tu pase y llévalo impreso o en tu teléfono.",
                },
                {
                  icon: CalendarCheck,
                  title: "3. Inscripción presencial",
                  body: "Acude a tu sede. El personal validará tu pase y tu pago si aplica.",
                },
              ].map((step) => {
                const Icon = step.icon;
                return (
                  <div key={step.title} className="poster-card p-5">
                    <Icon className="h-5 w-5 text-primary" />
                    <h3 className="mt-4 font-display text-xl uppercase text-ink">{step.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-ink/60">{step.body}</p>
                  </div>
                );
              })}
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
