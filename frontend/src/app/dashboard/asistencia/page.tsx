"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Sede { id: number; nombre: string; }
interface Clase {
  id: number | null;
  corrida_id: number | null;
  sede_id: number;
  sede_nombre: string;
  grupo_id: number;
  grupo_nombre: string;
  materia_nombre: string;
  tutor_id: number;
  tutor_nombre: string;
  fecha: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  estado: string;
  tutor_cubridor_id: number | null;
  tutor_cubridor_nombre: string | null;
  comentario: string | null;
  origen: string;
}
interface Tutor { id: number; nombre: string; apellido_paterno: string; apellido_materno: string | null; }
interface Grupo { id: number; nombre: string; materia_id: number; }

const ESTADOS = [
  { value: "pendiente", label: "Pendiente" },
  { value: "asistio", label: "Asistió" },
  { value: "retardo", label: "Retardo" },
  { value: "falta", label: "Falta" },
  { value: "justificada", label: "Justificada" },
  { value: "cancelada", label: "Cancelada" },
  { value: "cubierta", label: "Cubierta" },
];

function localDate() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function tutorName(tutor: Tutor) {
  return `${tutor.nombre} ${tutor.apellido_paterno} ${tutor.apellido_materno || ""}`.trim();
}

export default function AsistenciaPage() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [fecha, setFecha] = useState(localDate);
  const [sedeFilter, setSedeFilter] = useState("");
  const [selected, setSelected] = useState<Clase | null>(null);
  const [estado, setEstado] = useState("pendiente");
  const [cubridorId, setCubridorId] = useState("");
  const [comentario, setComentario] = useState("");
  const [error, setError] = useState("");
  const [manualOpen, setManualOpen] = useState(false);
  const [manualSedeId, setManualSedeId] = useState("");
  const [manualGrupoId, setManualGrupoId] = useState("");
  const [manualTutorId, setManualTutorId] = useState("");
  const [manualFecha, setManualFecha] = useState(fecha);
  const [manualInicio, setManualInicio] = useState("08:00");
  const [manualFin, setManualFin] = useState("09:00");
  const [manualEstado, setManualEstado] = useState("asistio");
  const [manualCubridorId, setManualCubridorId] = useState("");
  const [manualComentario, setManualComentario] = useState("");
  const [manualError, setManualError] = useState("");

  const isAdmin = user?.role === "admin";
  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes"], queryFn: async () => (await api.get("/sedes")).data });
  const { data, isLoading } = useQuery<Clase[]>({
    queryKey: ["asistencia", fecha, sedeFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ fecha });
      if (sedeFilter) params.set("sede_id", sedeFilter);
      return (await api.get(`/asistencia/clases?${params.toString()}`)).data;
    },
  });
  const { data: tutores } = useQuery<Tutor[]>({
    queryKey: ["tutores", selected?.sede_id],
    queryFn: async () => (await api.get(`/tutores?sede_id=${selected?.sede_id}`)).data,
    enabled: Boolean(selected),
  });
  const { data: manualGrupos } = useQuery<Grupo[]>({
    queryKey: ["grupos", manualSedeId],
    queryFn: async () => (await api.get(`/sedes/${manualSedeId}/grupos`)).data,
    enabled: manualOpen && Boolean(manualSedeId),
  });
  const { data: manualTutores } = useQuery<Tutor[]>({
    queryKey: ["tutores", manualSedeId],
    queryFn: async () => (await api.get(`/tutores?sede_id=${manualSedeId}`)).data,
    enabled: manualOpen && Boolean(manualSedeId),
  });

  const resumen = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const clase of data || []) counts[clase.estado] = (counts[clase.estado] || 0) + 1;
    return counts;
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!selected) throw new Error("Sin sesión");
      const body = {
        estado,
        tutor_cubridor_id: estado === "cubierta" ? Number(cubridorId) : null,
        comentario: comentario.trim() || null,
      };
      if (selected.id) return api.put(`/asistencia/sesiones/${selected.id}`, body);
      return api.post("/asistencia/sesiones", {
        corrida_id: selected.corrida_id,
        sede_id: selected.sede_id,
        grupo_id: selected.grupo_id,
        tutor_id: selected.tutor_id,
        fecha: selected.fecha,
        hora_inicio: selected.hora_inicio,
        hora_fin: selected.hora_fin,
        ...body,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asistencia"] });
      queryClient.invalidateQueries({ queryKey: ["mis-sesiones"] });
      setSelected(null);
      setError("");
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "No pudimos guardar la asistencia.");
    },
  });

  const manualMutation = useMutation({
    mutationFn: async () => api.post("/asistencia/sesiones", {
      corrida_id: null,
      sede_id: Number(manualSedeId),
      grupo_id: Number(manualGrupoId),
      tutor_id: Number(manualTutorId),
      fecha: manualFecha,
      hora_inicio: manualInicio,
      hora_fin: manualFin,
      estado: manualEstado,
      tutor_cubridor_id: manualEstado === "cubierta" ? Number(manualCubridorId) : null,
      comentario: manualComentario.trim() || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asistencia"] });
      queryClient.invalidateQueries({ queryKey: ["mis-sesiones"] });
      setManualOpen(false);
      setManualError("");
      setFecha(manualFecha);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setManualError(detail || "No pudimos crear la sesión manual.");
    },
  });

  function openClase(clase: Clase) {
    setSelected(clase);
    setEstado(clase.estado);
    setCubridorId(clase.tutor_cubridor_id ? String(clase.tutor_cubridor_id) : "");
    setComentario(clase.comentario || "");
    setError("");
  }

  function openManual() {
    const defaultSede = user?.sede_id ? String(user.sede_id) : sedeFilter || String(sedes?.[0]?.id || "");
    setManualSedeId(defaultSede);
    setManualGrupoId("");
    setManualTutorId("");
    setManualFecha(fecha);
    setManualInicio("08:00");
    setManualFin("09:00");
    setManualEstado("asistio");
    setManualCubridorId("");
    setManualComentario("");
    setManualError("");
    setManualOpen(true);
  }

  function submitManual() {
    if (!manualSedeId || !manualGrupoId || !manualTutorId || !manualFecha) {
      setManualError("Completa sede, grupo, tutor y fecha.");
      return;
    }
    if (manualInicio >= manualFin) {
      setManualError("La hora de inicio debe ser menor a la de fin.");
      return;
    }
    if (manualEstado === "cubierta" && !manualCubridorId) {
      setManualError("Selecciona el tutor que cubrió la clase.");
      return;
    }
    manualMutation.mutate();
  }

  const columns: Column<Clase>[] = [
    {
      key: "hora",
      header: "Horario",
      sortValue: (clase) => clase.hora_inicio,
      render: (clase) => <span className="font-mono text-xs font-semibold">{clase.hora_inicio} — {clase.hora_fin}</span>,
    },
    {
      key: "clase",
      header: "Clase",
      sortValue: (clase) => `${clase.materia_nombre} ${clase.grupo_nombre}`,
      searchValue: (clase) => [clase.materia_nombre, clase.grupo_nombre, clase.sede_nombre].join(" "),
      render: (clase) => (
        <div>
          <p className="font-semibold text-ink">{clase.materia_nombre || "Sin materia"}</p>
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">{clase.grupo_nombre} · {clase.sede_nombre}</p>
        </div>
      ),
    },
    {
      key: "tutor",
      header: "Tutor",
      sortValue: (clase) => clase.tutor_nombre,
      searchValue: (clase) => `${clase.tutor_nombre} ${clase.tutor_cubridor_nombre || ""}`,
      render: (clase) => (
        <div>
          <p className="text-sm font-semibold">{clase.tutor_nombre}</p>
          {clase.tutor_cubridor_nombre && (
            <p className="text-xs text-accent-deep">Cubridor: {clase.tutor_cubridor_nombre}</p>
          )}
        </div>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      sortValue: (clase) => clase.estado,
      render: (clase) => <StatusBadge status={clase.estado} />,
    },
    {
      key: "comentario",
      header: "Comentario",
      render: (clase) => <span className="line-clamp-2 text-xs text-ink/65">{clase.comentario || "—"}</span>,
    },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (clase) => (
        <Button size="sm" variant={clase.id ? "outline" : "default"} onClick={() => openClase(clase)}>
          {clase.id ? "Editar" : "Registrar"}
        </Button>
      ),
    },
  ];

  return (
    <AppShell title="Asistencia">
      <div className="space-y-6">
        <PageHeader
          title="Asistencia de tutores"
          description="Registra asistencia, retardos, faltas, justificaciones y clases cubiertas."
          actions={<Button onClick={openManual}>Nueva sesión manual</Button>}
        />

        <div className="poster-card grid gap-4 p-4 sm:grid-cols-[auto_auto_1fr] sm:items-end">
          <div className="space-y-2">
            <Label htmlFor="asistencia-fecha">Fecha</Label>
            <Input id="asistencia-fecha" type="date" value={fecha} onChange={(event) => setFecha(event.target.value)} />
          </div>
          {isAdmin && (
            <div className="space-y-2">
              <Label htmlFor="asistencia-sede">Sede</Label>
              <select
                id="asistencia-sede"
                className="h-10 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={sedeFilter}
                onChange={(event) => setSedeFilter(event.target.value)}
              >
                <option value="">Todas las sedes</option>
                {(sedes || []).map((sede) => <option key={sede.id} value={sede.id}>{sede.nombre}</option>)}
              </select>
            </div>
          )}
          <div className="flex flex-wrap gap-2 sm:justify-end">
            {[
              ["pendiente", "Pendientes"],
              ["asistio", "Asistieron"],
              ["falta", "Faltas"],
              ["cubierta", "Cubiertas"],
            ].map(([key, label]) => (
              <div key={key} className="border border-ink/15 bg-sand/40 px-3 py-2">
                <p className="font-mono text-[0.55rem] uppercase tracking-[0.08em] text-ink/45">{label}</p>
                <p className="font-display text-xl leading-none text-primary">{resumen[key] || 0}</p>
              </div>
            ))}
          </div>
        </div>

        <DataTable
          columns={columns}
          data={data}
          isLoading={isLoading}
          keyExtractor={(clase) => clase.id ?? `${clase.corrida_id}-${clase.grupo_id}-${clase.tutor_id}-${clase.fecha}-${clase.hora_inicio}`}
          searchPlaceholder="Buscar materia, grupo, tutor o sede"
          emptyMessage="No hay clases para esta fecha."
          initialSort={{ key: "hora", direction: "asc" }}
          filters={[
            {
              key: "estado",
              label: "Estado",
              options: ESTADOS,
              getValue: (clase) => clase.estado,
            },
            {
              key: "origen",
              label: "Origen",
              options: [
                { value: "automatica", label: "Automática" },
                { value: "manual", label: "Manual" },
              ],
              getValue: (clase) => clase.origen,
            },
          ]}
        />
      </div>

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Registrar asistencia</DialogTitle>
            <DialogDescription>
              {selected ? `${selected.materia_nombre} · ${selected.grupo_nombre} · ${selected.fecha} · ${selected.hora_inicio}–${selected.hora_fin}` : ""}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="sesion-estado">Estado</Label>
              <select
                id="sesion-estado"
                className="h-10 w-full border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={estado}
                onChange={(event) => {
                  setEstado(event.target.value);
                  if (event.target.value !== "cubierta") setCubridorId("");
                }}
              >
                {ESTADOS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </div>

            {estado === "cubierta" && (
              <div className="space-y-2">
                <Label htmlFor="sesion-cubridor">Tutor que cubrió</Label>
                <select
                  id="sesion-cubridor"
                  className="h-10 w-full border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                  value={cubridorId}
                  onChange={(event) => setCubridorId(event.target.value)}
                >
                  <option value="">Selecciona un tutor</option>
                  {(tutores || []).filter((tutor) => tutor.id !== selected?.tutor_id).map((tutor) => (
                    <option key={tutor.id} value={tutor.id}>{tutorName(tutor)}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="sesion-comentario">Comentario</Label>
              <textarea
                id="sesion-comentario"
                rows={3}
                className="w-full border border-ink/25 bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:border-primary"
                value={comentario}
                onChange={(event) => setComentario(event.target.value)}
                placeholder="Opcional: incidencia, justificación o nota para el tutor."
              />
            </div>
            {error && <p role="alert" className="text-sm font-semibold text-accent-deep">{error}</p>}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setSelected(null)}>Cancelar</Button>
            <Button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || (estado === "cubierta" && !cubridorId)}
            >
              {saveMutation.isPending ? "Guardando..." : "Guardar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={manualOpen} onOpenChange={(open) => !open && setManualOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nueva sesión manual</DialogTitle>
            <DialogDescription>Agrega una clase que no forma parte del horario publicado.</DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="manual-sede">Sede</Label>
              <select
                id="manual-sede"
                className="h-10 w-full border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={manualSedeId}
                disabled={!isAdmin}
                onChange={(event) => {
                  setManualSedeId(event.target.value);
                  setManualGrupoId("");
                  setManualTutorId("");
                  setManualCubridorId("");
                }}
              >
                <option value="">Selecciona una sede</option>
                {(sedes || []).map((sede) => <option key={sede.id} value={sede.id}>{sede.nombre}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="manual-fecha">Fecha</Label>
              <Input id="manual-fecha" type="date" value={manualFecha} onChange={(event) => setManualFecha(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="manual-grupo">Grupo</Label>
              <select
                id="manual-grupo"
                className="h-10 w-full border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={manualGrupoId}
                onChange={(event) => setManualGrupoId(event.target.value)}
              >
                <option value="">Selecciona un grupo</option>
                {(manualGrupos || []).map((grupo) => <option key={grupo.id} value={grupo.id}>{grupo.nombre}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="manual-tutor">Tutor titular</Label>
              <select
                id="manual-tutor"
                className="h-10 w-full border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={manualTutorId}
                onChange={(event) => {
                  setManualTutorId(event.target.value);
                  if (event.target.value === manualCubridorId) setManualCubridorId("");
                }}
              >
                <option value="">Selecciona un tutor</option>
                {(manualTutores || []).map((tutor) => <option key={tutor.id} value={tutor.id}>{tutorName(tutor)}</option>)}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="manual-inicio">Desde</Label>
              <Input id="manual-inicio" type="time" step={3600} value={manualInicio} onChange={(event) => setManualInicio(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="manual-fin">Hasta</Label>
              <Input id="manual-fin" type="time" step={3600} value={manualFin} onChange={(event) => setManualFin(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="manual-estado">Estado</Label>
              <select
                id="manual-estado"
                className="h-10 w-full border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={manualEstado}
                onChange={(event) => {
                  setManualEstado(event.target.value);
                  if (event.target.value !== "cubierta") setManualCubridorId("");
                }}
              >
                {ESTADOS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </div>
            {manualEstado === "cubierta" && (
              <div className="space-y-2">
                <Label htmlFor="manual-cubridor">Tutor que cubrió</Label>
                <select
                  id="manual-cubridor"
                  className="h-10 w-full border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                  value={manualCubridorId}
                  onChange={(event) => setManualCubridorId(event.target.value)}
                >
                  <option value="">Selecciona un tutor</option>
                  {(manualTutores || []).filter((tutor) => String(tutor.id) !== manualTutorId).map((tutor) => (
                    <option key={tutor.id} value={tutor.id}>{tutorName(tutor)}</option>
                  ))}
                </select>
              </div>
            )}
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="manual-comentario">Comentario</Label>
              <textarea
                id="manual-comentario"
                rows={3}
                className="w-full border border-ink/25 bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:border-primary"
                value={manualComentario}
                onChange={(event) => setManualComentario(event.target.value)}
                placeholder="Opcional."
              />
            </div>
          </div>
          {manualError && <p role="alert" className="mt-4 text-sm font-semibold text-accent-deep">{manualError}</p>}
          <DialogFooter>
            <Button variant="outline" onClick={() => setManualOpen(false)}>Cancelar</Button>
            <Button onClick={submitManual} disabled={manualMutation.isPending}>
              {manualMutation.isPending ? "Guardando..." : "Crear sesión"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
