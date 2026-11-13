"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Corrida { id: number; sede_id: number | null; estado: string; aprobada: boolean; publicada: boolean; fecha_inicio: string | null; fecha_fin: string | null; metricas_optimizacion: unknown; }
interface Sede { id: number; nombre: string; }
interface PeriodTarget { corrida: Corrida; mode: "publish" | "generate"; }

function localDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function addDays(value: string, days: number) {
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(year, month - 1, day + days);
  return localDate(date);
}

export default function PublicarPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<Corrida[]>({ queryKey: ["corridas"], queryFn: async () => (await api.get("/corridas", { headers })).data });
  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes", { headers })).data });
  const sedeName = new Map((sedes || []).map((sede) => [sede.id, sede.nombre]));

  const [periodTarget, setPeriodTarget] = useState<PeriodTarget | null>(null);
  const [fechaInicio, setFechaInicio] = useState("");
  const [fechaFin, setFechaFin] = useState("");
  const [periodError, setPeriodError] = useState("");
  const [notice, setNotice] = useState("");

  const approveMutation = useMutation({ mutationFn: async (id: number) => api.post(`/corridas/${id}/aprobar`, {}, { headers }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }) });
  const publishMutation = useMutation({
    mutationFn: async ({ id, inicio, fin }: { id: number; inicio: string; fin: string }) =>
      api.post(`/corridas/${id}/publicar`, { fecha_inicio: inicio, fecha_fin: fin }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["corridas"] });
      queryClient.invalidateQueries({ queryKey: ["asistencia"] });
      queryClient.invalidateQueries({ queryKey: ["mis-sesiones"] });
      setPeriodTarget(null);
      setNotice("Horario publicado y sesiones generadas para el periodo.");
    },
    onError: (err: unknown) => setPeriodError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "No pudimos publicar el horario."),
  });
  const generateMutation = useMutation({
    mutationFn: async ({ id, inicio, fin }: { id: number; inicio: string; fin: string }) =>
      (await api.post(`/corridas/${id}/generar-sesiones`, { fecha_inicio: inicio, fecha_fin: fin }, { headers })).data,
    onSuccess: (data: { sesiones_generadas: number }) => {
      queryClient.invalidateQueries({ queryKey: ["corridas"] });
      queryClient.invalidateQueries({ queryKey: ["asistencia"] });
      queryClient.invalidateQueries({ queryKey: ["mis-sesiones"] });
      setPeriodTarget(null);
      setNotice(`Se generaron ${data.sesiones_generadas} sesiones nuevas.`);
    },
    onError: (err: unknown) => setPeriodError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "No pudimos generar las sesiones."),
  });

  function openPeriod(corrida: Corrida, mode: "publish" | "generate") {
    const start = corrida.fecha_inicio || localDate();
    setPeriodTarget({ corrida, mode });
    setFechaInicio(start);
    setFechaFin(corrida.fecha_fin || addDays(start, 28));
    setPeriodError("");
  }

  function submitPeriod() {
    if (!periodTarget) return;
    if (!fechaInicio || !fechaFin || fechaInicio > fechaFin) {
      setPeriodError("Define un periodo válido, con inicio menor o igual al fin.");
      return;
    }
    if (periodTarget.mode === "publish") {
      publishMutation.mutate({ id: periodTarget.corrida.id, inicio: fechaInicio, fin: fechaFin });
    } else {
      generateMutation.mutate({ id: periodTarget.corrida.id, inicio: fechaInicio, fin: fechaFin });
    }
  }

  const columns: Column<Corrida>[] = [
    {
      key: "id",
      header: "Corrida",
      sortValue: (item) => item.id,
      render: (item) => <span className="font-mono text-xs font-bold">#{item.id}</span>,
    },
    {
      key: "sede_id",
      header: "Sede",
      sortValue: (item) => (item.sede_id ? sedeName.get(item.sede_id) || "" : ""),
      render: (item) => (item.sede_id ? sedeName.get(item.sede_id) || `Sede ${item.sede_id}` : "Sin sede"),
    },
    { key: "estado", header: "Estado", sortValue: (item) => item.estado, render: (item) => <StatusBadge status={item.estado} /> },
    {
      key: "aprobada",
      header: "Aprobada",
      sortValue: (item) => (item.aprobada ? 1 : 0),
      render: (item) => <StatusBadge status={item.aprobada ? "APROBADA" : "PENDIENTE"} />,
    },
    {
      key: "publicada",
      header: "Publicada",
      sortValue: (item) => (item.publicada ? 1 : 0),
      render: (item) => <StatusBadge status={item.publicada ? "PUBLICADA" : "PENDIENTE"} />,
    },
    {
      key: "periodo",
      header: "Periodo",
      sortValue: (item) => item.fecha_inicio || "",
      render: (item) => item.fecha_inicio && item.fecha_fin ? (
        <span className="font-mono text-xs">{item.fecha_inicio} — {item.fecha_fin}</span>
      ) : <span className="text-xs text-ink/45">Sin periodo</span>,
    },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <div className="flex justify-end gap-2">
          <Button size="sm" variant="outline" onClick={() => approveMutation.mutate(item.id)} disabled={item.aprobada}>Aprobar</Button>
          {item.publicada ? (
            <Button size="sm" variant="outline" onClick={() => openPeriod(item, "generate")}>Generar sesiones</Button>
          ) : (
            <Button size="sm" onClick={() => openPeriod(item, "publish")} disabled={!item.aprobada}>Publicar</Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <AppShell title="Publicar horarios">
      <div className="space-y-6">
        <PageHeader title="Publicar horarios" description="Revisa las corridas generadas, define su periodo, apruébalas y hazlas visibles para estudiantes y tutores." />
        {notice && <p role="status" className="border border-accent/30 bg-accent/10 px-4 py-3 text-sm font-semibold text-accent-deep">{notice}</p>}
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin corridas" description="Cuando se genere una corrida para tu sede aparecerá aquí para su aprobación." />
        ) : (
          <DataTable
            columns={columns}
            data={data}
            isLoading={isLoading}
            keyExtractor={(item) => item.id}
            searchPlaceholder="Buscar por folio o sede"
            initialSort={{ key: "id", direction: "desc" }}
            filters={[
              {
                key: "sede_id",
                label: "Sede",
                options: (sedes || []).map((sede) => ({ value: String(sede.id), label: sede.nombre })),
                getValue: (item) => (item.sede_id ? String(item.sede_id) : ""),
              },
              {
                key: "estado",
                label: "Estado",
                options: [
                  { value: "PENDIENTE", label: "Pendiente" },
                  { value: "PROCESANDO", label: "Procesando" },
                  { value: "COMPLETADO", label: "Completado" },
                  { value: "ERROR", label: "Error" },
                ],
                getValue: (item) => item.estado,
              },
              {
                key: "publicada",
                label: "Publicación",
                options: [
                  { value: "true", label: "Publicadas" },
                  { value: "false", label: "Sin publicar" },
                ],
                getValue: (item) => String(item.publicada),
              },
            ]}
          />
        )}
      </div>

      <Dialog open={Boolean(periodTarget)} onOpenChange={(open) => !open && setPeriodTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{periodTarget?.mode === "generate" ? "Generar sesiones" : "Publicar horario"}</DialogTitle>
            <DialogDescription>
              Define el periodo que cubrirá esta corrida. Las clases se repetirán cada semana según el horario asignado.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="periodo-inicio">Fecha de inicio</Label>
              <Input id="periodo-inicio" type="date" value={fechaInicio} onChange={(event) => setFechaInicio(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="periodo-fin">Fecha de fin</Label>
              <Input id="periodo-fin" type="date" value={fechaFin} onChange={(event) => setFechaFin(event.target.value)} />
            </div>
          </div>
          {periodError && <p role="alert" className="mt-4 text-sm font-semibold text-accent-deep">{periodError}</p>}
          <DialogFooter>
            <Button variant="outline" onClick={() => setPeriodTarget(null)}>Cancelar</Button>
            <Button onClick={submitPeriod} disabled={publishMutation.isPending || generateMutation.isPending}>
              {publishMutation.isPending || generateMutation.isPending
                ? "Procesando..."
                : periodTarget?.mode === "generate" ? "Generar" : "Publicar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
