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

  function openClase(clase: Clase) {
    setSelected(clase);
    setEstado(clase.estado);
    setCubridorId(clase.tutor_cubridor_id ? String(clase.tutor_cubridor_id) : "");
    setComentario(clase.comentario || "");
    setError("");
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
        <PageHeader title="Asistencia de tutores" description="Registra asistencia, retardos, faltas, justificaciones y clases cubiertas." />

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
    </AppShell>
  );
}
