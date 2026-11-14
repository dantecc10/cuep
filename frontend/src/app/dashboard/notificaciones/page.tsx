"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bell, Mail, Play, RefreshCw, Save } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Pagination } from "@/components/ui/pagination";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Plantilla {
  id: number;
  clave: string;
  nombre: string;
  asunto: string;
  cuerpo_texto: string;
  cuerpo_html: string | null;
  variables: unknown;
  activo: boolean;
  updated_at: string;
}

interface Outbox {
  id: number;
  plantilla_clave: string | null;
  destinatario_email: string;
  asunto: string;
  estado: string;
  intentos: number;
  ultimo_error: string | null;
  programado_para: string;
  enviado_at: string | null;
  created_at: string;
}

interface OutboxPage {
  items: Outbox[];
  total: number;
  page: number;
  page_size: number;
}

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export default function NotificacionesPage() {
  const token = useAuthStore((s) => s.token);
  const role = useAuthStore((s) => s.user?.role || "");
  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);
  const [tab, setTab] = useState<"plantillas" | "outbox">("plantillas");
  const [selected, setSelected] = useState<Plantilla | null>(null);
  const [form, setForm] = useState({ nombre: "", asunto: "", cuerpo_texto: "", cuerpo_html: "", activo: true });
  const [outboxPage, setOutboxPage] = useState(1);
  const [outboxEstado, setOutboxEstado] = useState("");
  const [busy, setBusy] = useState(false);

  const { data: plantillas, isLoading: loadingPlantillas, refetch: refetchPlantillas } = useQuery<Plantilla[]>({
    queryKey: ["notificacion-plantillas"],
    queryFn: async () => (await api.get("/notificaciones/plantillas", { headers })).data,
    enabled: Boolean(token && role === "admin"),
  });

  const { data: outbox, isLoading: loadingOutbox, refetch: refetchOutbox } = useQuery<OutboxPage>({
    queryKey: ["notificacion-outbox", outboxPage, outboxEstado],
    queryFn: async () =>
      (
        await api.get("/notificaciones/outbox", {
          headers,
          params: { page: outboxPage, page_size: 25, estado: outboxEstado || undefined },
        })
      ).data,
    enabled: Boolean(token && role === "admin"),
  });

  function editPlantilla(plantilla: Plantilla) {
    setSelected(plantilla);
    setForm({
      nombre: plantilla.nombre,
      asunto: plantilla.asunto,
      cuerpo_texto: plantilla.cuerpo_texto,
      cuerpo_html: plantilla.cuerpo_html || "",
      activo: plantilla.activo,
    });
  }

  async function savePlantilla(event: React.FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setBusy(true);
    try {
      const response = await api.put(
        `/notificaciones/plantillas/${selected.clave}`,
        {
          ...form,
          cuerpo_html: form.cuerpo_html || null,
        },
        { headers },
      );
      setSelected(response.data);
      toast.success("Plantilla actualizada.");
      await refetchPlantillas();
    } catch {
      toast.error("No pudimos guardar la plantilla.");
    } finally {
      setBusy(false);
    }
  }

  async function processOutbox() {
    setBusy(true);
    try {
      const response = await api.post("/notificaciones/procesar", undefined, { headers });
      const simulados = response.data.simulados ?? 0;
      toast.success(
        `Procesadas: ${response.data.procesados} · enviadas: ${response.data.enviados} · fallidas: ${response.data.fallidos}${simulados ? ` · simuladas: ${simulados}` : ""}`,
      );
      await refetchOutbox();
    } catch {
      toast.error("No pudimos procesar la salida de notificaciones.");
    } finally {
      setBusy(false);
    }
  }

  async function retry(id: number) {
    setBusy(true);
    try {
      await api.post(`/notificaciones/outbox/${id}/reintentar`, undefined, { headers });
      toast.success("Notificación marcada para reintento.");
      await refetchOutbox();
    } catch {
      toast.error("No pudimos reintentar la notificación.");
    } finally {
      setBusy(false);
    }
  }

  if (role !== "admin") {
    return (
      <AppShell title="Notificaciones">
        <div className="poster-card p-8">
          <p className="type-kicker">Acceso restringido</p>
          <p className="mt-3 font-editorial text-xl text-ink/65">
            Sólo administración puede gestionar plantillas y la salida de correos.
          </p>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="Notificaciones">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Correo transaccional"
          title="Notificaciones"
          description="Edita las plantillas y revisa la salida de correos del proceso de inscripción."
          actions={
            tab === "outbox" ? (
              <Button onClick={processOutbox} disabled={busy}>
                <Play className="mr-2 h-4 w-4" /> Procesar pendientes
              </Button>
            ) : undefined
          }
        />

        <div className="flex gap-2 border-b border-ink/15 pb-2">
          <Button
            variant={tab === "plantillas" ? "default" : "outline"}
            size="sm"
            onClick={() => setTab("plantillas")}
          >
            <Bell className="mr-1.5 h-3.5 w-3.5" /> Plantillas
          </Button>
          <Button
            variant={tab === "outbox" ? "default" : "outline"}
            size="sm"
            onClick={() => setTab("outbox")}
          >
            <Mail className="mr-1.5 h-3.5 w-3.5" /> Salida
          </Button>
        </div>

        {tab === "plantillas" ? (
          <div className="grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
            <Card>
              <CardHeader><CardTitle>Plantillas</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {loadingPlantillas ? (
                  <div className="h-40 animate-pulse bg-ink/10" />
                ) : (plantillas || []).map((plantilla) => (
                  <button
                    key={plantilla.clave}
                    type="button"
                    onClick={() => editPlantilla(plantilla)}
                    className={`w-full border p-3 text-left transition ${
                      selected?.clave === plantilla.clave ? "border-primary bg-primary/5" : "border-ink/15 hover:border-ink/40"
                    }`}
                  >
                    <p className="font-semibold text-ink">{plantilla.nombre}</p>
                    <p className="mt-1 font-mono text-[0.62rem] uppercase tracking-[0.06em] text-ink/45">
                      {plantilla.clave}
                    </p>
                    <div className="mt-2 flex items-center justify-between gap-2">
                      <span className="truncate text-xs text-ink/55">{plantilla.asunto}</span>
                      <StatusBadge status={plantilla.activo ? "activo" : "baja"} />
                    </div>
                  </button>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{selected ? selected.nombre : "Selecciona una plantilla"}</CardTitle>
              </CardHeader>
              <CardContent>
                {selected ? (
                  <form onSubmit={savePlantilla} className="space-y-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="nombre">Nombre</Label>
                      <Input id="nombre" className="h-10" value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} required />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="asunto">Asunto</Label>
                      <Input id="asunto" className="h-10" value={form.asunto} onChange={(event) => setForm({ ...form, asunto: event.target.value })} required />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="cuerpo_texto">Cuerpo de texto</Label>
                      <textarea
                        id="cuerpo_texto"
                        rows={7}
                        className="w-full border border-ink/30 bg-surface px-3 py-2 font-mono text-xs text-ink outline-none focus-visible:border-primary"
                        value={form.cuerpo_texto}
                        onChange={(event) => setForm({ ...form, cuerpo_texto: event.target.value })}
                        required
                      />
                      <p className="text-xs text-ink/45">
                        Variables disponibles: $nombre, $matricula, $sede, $monto, $moneda, $recibo, $motivo.
                      </p>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="cuerpo_html">Cuerpo HTML (opcional)</Label>
                      <textarea
                        id="cuerpo_html"
                        rows={5}
                        className="w-full border border-ink/30 bg-surface px-3 py-2 font-mono text-xs text-ink outline-none focus-visible:border-primary"
                        value={form.cuerpo_html}
                        onChange={(event) => setForm({ ...form, cuerpo_html: event.target.value })}
                      />
                    </div>
                    <label className="flex items-center gap-2 text-sm text-ink">
                      <input
                        type="checkbox"
                        className="h-4 w-4 accent-[#A92730]"
                        checked={form.activo}
                        onChange={(event) => setForm({ ...form, activo: event.target.checked })}
                      />
                      Plantilla activa
                    </label>
                    <Button type="submit" disabled={busy}>
                      <Save className="mr-2 h-4 w-4" /> {busy ? "Guardando..." : "Guardar plantilla"}
                    </Button>
                  </form>
                ) : (
                  <p className="text-sm text-ink/55">Elige una plantilla de la lista para editarla.</p>
                )}
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="poster-card flex flex-wrap items-center justify-between gap-3 p-4">
              <select
                aria-label="Filtrar por estado"
                className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={outboxEstado}
                onChange={(event) => { setOutboxEstado(event.target.value); setOutboxPage(1); }}
              >
                <option value="">Estado: todos</option>
                <option value="pendiente">Pendiente</option>
                <option value="enviado">Enviado</option>
                <option value="simulado">Simulado</option>
                <option value="error">Error</option>
              </select>
              <span className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/45">
                {outbox?.total || 0} notificaciones
              </span>
            </div>

            {loadingOutbox ? (
              <div className="h-52 animate-pulse bg-ink/10" />
            ) : (outbox?.items || []).length === 0 ? (
              <div className="border border-dashed border-ink/25 bg-surface px-4 py-10 text-center">
                <p className="font-editorial text-base text-ink/55">No hay notificaciones en la salida.</p>
              </div>
            ) : (
              <div className="poster-card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[720px] text-sm">
                    <thead className="border-b border-ink bg-paper/70">
                      <tr>
                        {["Correo", "Plantilla", "Estado", "Programada", "Error", ""].map((header) => (
                          <th key={header} className="px-4 py-3 text-left font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-ink">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(outbox?.items || []).map((item) => (
                        <tr key={item.id} className="border-b border-ink/10 last:border-b-0">
                          <td className="px-4 py-3">
                            <p className="font-semibold text-ink">{item.destinatario_email}</p>
                            <p className="text-xs text-ink/50">{item.asunto}</p>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-ink/65">{item.plantilla_clave || "—"}</td>
                          <td className="px-4 py-3"><StatusBadge status={item.estado} /></td>
                          <td className="px-4 py-3 text-xs text-ink/60">{formatDate(item.programado_para)}</td>
                          <td className="px-4 py-3 text-xs text-primary">{item.ultimo_error || "—"}</td>
                          <td className="px-4 py-3 text-right">
                            {item.estado !== "enviado" ? (
                              <Button size="sm" variant="outline" onClick={() => retry(item.id)} disabled={busy}>
                                <RefreshCw className="mr-1 h-3.5 w-3.5" /> Reintentar
                              </Button>
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            <Pagination
              page={outboxPage}
              totalPages={Math.max(1, Math.ceil((outbox?.total || 0) / (outbox?.page_size || 25)))}
              onPageChange={setOutboxPage}
            />
          </div>
        )}
      </div>
    </AppShell>
  );
}
