"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { StatusBadge } from "@/components/shared/status-badge";

interface Sesion {
  id: number;
  sede_nombre: string;
  grupo_nombre: string;
  materia_nombre: string;
  tutor_nombre: string;
  tutor_cubridor_nombre: string | null;
  fecha: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  estado: string;
  comentario: string | null;
  rol: "titular" | "cubridor";
  impartida_por_mi: boolean;
}
interface Respuesta {
  resumen: {
    total: number;
    impartidas: number;
    asistio: number;
    retardo: number;
    falta: number;
    justificada: number;
    cancelada: number;
    cubierta: number;
    pendiente: number;
  };
  sesiones: Sesion[];
}

const ESTADOS = [
  { value: "pendiente", label: "Pendiente" },
  { value: "asistio", label: "Asistió" },
  { value: "retardo", label: "Retardo" },
  { value: "falta", label: "Falta" },
  { value: "justificada", label: "Justificada" },
  { value: "cancelada", label: "Cancelada" },
  { value: "cubierta", label: "Cubierta" },
];

function formatFecha(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-MX", { weekday: "short", day: "2-digit", month: "short" }).format(new Date(year, month - 1, day));
}

export default function MiHorarioPage() {
  const { data, isLoading } = useQuery<Respuesta>({
    queryKey: ["mis-sesiones"],
    queryFn: async () => (await api.get("/asistencia/mia")).data,
  });

  const resumen = data?.resumen;
  const columns: Column<Sesion>[] = [
    {
      key: "fecha",
      header: "Fecha",
      sortValue: (sesion) => sesion.fecha,
      render: (sesion) => (
        <div>
          <p className="text-sm font-semibold text-ink">{formatFecha(sesion.fecha)}</p>
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">{sesion.hora_inicio} — {sesion.hora_fin}</p>
        </div>
      ),
    },
    {
      key: "clase",
      header: "Clase",
      sortValue: (sesion) => `${sesion.materia_nombre} ${sesion.grupo_nombre}`,
      searchValue: (sesion) => [sesion.materia_nombre, sesion.grupo_nombre, sesion.sede_nombre, sesion.comentario].filter(Boolean).join(" "),
      render: (sesion) => (
        <div>
          <p className="font-semibold text-ink">{sesion.materia_nombre || "Sin materia"}</p>
          <p className="font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">{sesion.grupo_nombre} · {sesion.sede_nombre}</p>
        </div>
      ),
    },
    {
      key: "rol",
      header: "Rol",
      sortValue: (sesion) => sesion.rol,
      render: (sesion) => (
        <div>
          <p className="text-xs font-semibold capitalize text-ink">{sesion.rol}</p>
          {sesion.rol === "titular" && sesion.tutor_cubridor_nombre && (
            <p className="text-xs text-accent-deep">Cubrió: {sesion.tutor_cubridor_nombre}</p>
          )}
        </div>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      sortValue: (sesion) => sesion.estado,
      render: (sesion) => <StatusBadge status={sesion.estado} />,
    },
    {
      key: "comentario",
      header: "Comentario",
      render: (sesion) => <span className="line-clamp-2 text-xs text-ink/65">{sesion.comentario || "—"}</span>,
    },
  ];

  return (
    <AppShell title="Mi horario">
      <div className="space-y-6">
        <PageHeader title="Mi horario" description="Tus asesorías publicadas, la asistencia registrada y las clases que has cubierto." />

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {[
            ["Impartidas", resumen?.impartidas || 0],
            ["Asistencias", resumen?.asistio || 0],
            ["Retardos", resumen?.retardo || 0],
            ["Faltas", resumen?.falta || 0],
            ["Cubiertas", resumen?.cubierta || 0],
            ["Pendientes", resumen?.pendiente || 0],
          ].map(([label, value]) => (
            <div key={label} className="poster-card p-4">
              <p className="font-mono text-[0.58rem] uppercase tracking-[0.1em] text-ink/45">{label}</p>
              <p className="mt-1 font-display text-3xl leading-none text-primary">{value}</p>
            </div>
          ))}
        </div>

        <DataTable
          columns={columns}
          data={data?.sesiones}
          isLoading={isLoading}
          keyExtractor={(sesion) => sesion.id}
          searchPlaceholder="Buscar materia, grupo o comentario"
          emptyMessage="Cuando coordinación publique horarios y registre asistencia, aparecerá aquí."
          initialSort={{ key: "fecha", direction: "desc" }}
          filters={[
            { key: "estado", label: "Estado", options: ESTADOS, getValue: (sesion) => sesion.estado },
            {
              key: "rol",
              label: "Rol",
              options: [
                { value: "titular", label: "Titular" },
                { value: "cubridor", label: "Cubridor" },
              ],
              getValue: (sesion) => sesion.rol,
            },
          ]}
        />
      </div>
    </AppShell>
  );
}
