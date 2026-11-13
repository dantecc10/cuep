"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import { StatusBadge } from "@/components/shared/status-badge";

interface Kpi { id: string; label: string; value: number; hint: string; suffix?: string; }
interface EstadoMetric { estado: string; label: string; total: number; }
interface SemanaMetric {
  semana: string;
  label: string;
  total: number;
  atendidas: number;
  asistio: number;
  retardo: number;
  falta: number;
  justificada: number;
  cubierta: number;
  pendiente: number;
  cancelada: number;
}
interface SedeMetric { sede_id: number; sede: string; total: number; atendidas: number; faltas: number; cubiertas: number; pendientes: number; tasa: number; }
interface CargaTutor { tutor_id: number; tutor: string; asignadas: number; impartidas: number; faltas: number; cubiertas: number; total: number; }
interface Proxima { id: number; fecha: string; hora_inicio: string; hora_fin: string; grupo: string; estado: string; rol: string; }
interface Metrics {
  rol: string;
  alcance: string;
  periodo: { desde: string; hasta: string };
  kpis: Kpi[];
  asistencia: { por_estado: EstadoMetric[]; por_semana: SemanaMetric[]; por_sede: SedeMetric[] };
  carga_tutores: CargaTutor[];
  proximas: Proxima[];
  resumen: { total: number; atendidas: number; marcadas: number; tasa: number };
}

const COLORS = {
  asistio: "#3CB6BF",
  retardo: "#E8B83E",
  falta: "#A92730",
  justificada: "#4611A0",
  cubierta: "#146F78",
  pendiente: "#B99A6F",
  cancelada: "#6B7280",
};

const CHART_TOOLTIP = {
  contentStyle: { background: "#FFFDFC", border: "1px solid #171313", borderRadius: 4, fontSize: 12 },
  labelStyle: { fontWeight: 700, color: "#171313" },
};

function number(value: number) {
  return new Intl.NumberFormat("es-MX").format(value);
}

function formatDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("es-MX", { day: "2-digit", month: "short" }).format(new Date(year, month - 1, day));
}

export function MetricsPanel({ role }: { role: string }) {
  const enabled = ["admin", "coordinador", "subcoordinador", "tutor"].includes(role);
  const { data, isLoading, isError } = useQuery<Metrics>({
    queryKey: ["dashboard-metrics", role],
    queryFn: async () => (await api.get("/dashboard/metrics")).data,
    enabled,
  });

  if (!enabled) return null;
  if (isLoading) {
    return (
      <section className="space-y-4">
        <div className="h-24 animate-pulse border border-ink/15 bg-sand" />
        <div className="grid gap-4 md:grid-cols-2">
          <div className="h-72 animate-pulse border border-ink/15 bg-sand" />
          <div className="h-72 animate-pulse border border-ink/15 bg-sand" />
        </div>
      </section>
    );
  }
  if (isError || !data) {
    return <p className="border border-accent/30 bg-accent/10 px-4 py-3 text-sm font-semibold text-accent-deep">No pudimos cargar las métricas del panel.</p>;
  }

  const estados = data.asistencia.por_estado.filter((item) => item.total > 0);
  const semanas = data.asistencia.por_semana;
  const isTutor = data.rol === "tutor";
  const scopeLabel = data.alcance === "global" ? "Vista global" : data.alcance === "sede" ? "Vista de sede" : "Vista personal";

  return (
    <section className="space-y-5">
      <div className="flex flex-col gap-2 border-b border-ink/15 pb-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="type-label text-ink/40">Pulso del colectivo</p>
          <h2 className="mt-1 font-display text-3xl uppercase text-ink">Métricas de asistencia</h2>
        </div>
        <div className="text-left sm:text-right">
          <p className="font-mono text-[0.6rem] uppercase tracking-[0.1em] text-ink/45">{scopeLabel}</p>
          <p className="mt-1 font-mono text-[0.6rem] text-ink/35">{formatDate(data.periodo.desde)} — {formatDate(data.periodo.hasta)}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {data.kpis.map((kpi) => (
          <div key={kpi.id} className="poster-card p-4">
            <p className="font-mono text-[0.56rem] uppercase leading-tight tracking-[0.08em] text-ink/45">{kpi.label}</p>
            <p className="mt-2 font-display text-3xl leading-none text-primary">
              {number(kpi.value)}{kpi.suffix || ""}
            </p>
            <p className="mt-2 text-[0.68rem] leading-snug text-ink/50">{kpi.hint}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
        <div className="poster-card p-5">
          <div className="flex items-baseline justify-between gap-3">
            <div>
              <p className="type-kicker">Tendencia</p>
              <h3 className="mt-1 font-display text-2xl uppercase text-ink">Asistencia por semana</h3>
            </div>
            <span className="font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/40">{semanas.length} semanas</span>
          </div>
          <div className="mt-4 h-72 w-full">
            {semanas.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={semanas} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                  <CartesianGrid stroke="#171313" strokeOpacity={0.1} vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#171313" }} tickLine={false} axisLine={{ stroke: "#171313", strokeOpacity: 0.2 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#171313" }} tickLine={false} axisLine={false} />
                  <Tooltip {...CHART_TOOLTIP} />
                  <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                  <Bar dataKey="asistio" name="Asistió" stackId="a" fill={COLORS.asistio} />
                  <Bar dataKey="retardo" name="Retardo" stackId="a" fill={COLORS.retardo} />
                  <Bar dataKey="cubierta" name="Cubierta" stackId="a" fill={COLORS.cubierta} />
                  <Bar dataKey="justificada" name="Justificada" stackId="a" fill={COLORS.justificada} />
                  <Bar dataKey="falta" name="Falta" stackId="a" fill={COLORS.falta} />
                  <Bar dataKey="pendiente" name="Pendiente" stackId="a" fill={COLORS.pendiente} radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="grid h-full place-items-center border border-dashed border-ink/20 bg-sand/30 text-sm text-ink/50">Sin sesiones en el periodo.</div>
            )}
          </div>
        </div>

        <div className="poster-card p-5">
          <div>
            <p className="type-kicker">Composición</p>
            <h3 className="mt-1 font-display text-2xl uppercase text-ink">Estados</h3>
          </div>
          <div className="mt-2 h-72 w-full">
            {estados.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={estados} dataKey="total" nameKey="label" innerRadius={52} outerRadius={82} paddingAngle={2} stroke="#FFFDFC" strokeWidth={2}>
                    {estados.map((item) => <Cell key={item.estado} fill={COLORS[item.estado as keyof typeof COLORS] || COLORS.pendiente} />)}
                  </Pie>
                  <Tooltip {...CHART_TOOLTIP} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="grid h-full place-items-center border border-dashed border-ink/20 bg-sand/30 text-sm text-ink/50">Sin registros.</div>
            )}
          </div>
        </div>
      </div>

      {isTutor ? (
        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="poster-card p-5">
            <p className="type-kicker">Tu carga</p>
            <h3 className="mt-1 font-display text-2xl uppercase text-ink">Resumen personal</h3>
            <div className="mt-4 space-y-3">
              {[
                ["Clases atendidas", data.resumen.atendidas, data.resumen.marcadas],
                ["Tasa de asistencia", data.resumen.tasa, 100],
              ].map(([label, value, max]) => (
                <div key={String(label)}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-ink">{label}</span>
                    <span className="font-mono text-ink/55">{number(Number(value))}{label === "Tasa de asistencia" ? "%" : ""}</span>
                  </div>
                  <div className="mt-1 h-2 border border-ink/15 bg-sand">
                    <div className="h-full bg-accent" style={{ width: `${Math.min(100, (Number(value) / Math.max(1, Number(max))) * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="poster-card p-5">
            <p className="type-kicker">Lo que viene</p>
            <h3 className="mt-1 font-display text-2xl uppercase text-ink">Próximas clases</h3>
            <div className="mt-4 space-y-2">
              {data.proximas.length ? data.proximas.map((item) => (
                <div key={item.id} className="flex items-center justify-between gap-3 border border-ink/15 bg-sand/25 px-3 py-2">
                  <div>
                    <p className="text-sm font-semibold text-ink">{item.grupo}</p>
                    <p className="font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">{formatDate(item.fecha)} · {item.hora_inicio}–{item.hora_fin} · {item.rol}</p>
                  </div>
                  <StatusBadge status={item.estado} />
                </div>
              )) : <p className="text-sm text-ink/50">No tienes clases próximas pendientes.</p>}
            </div>
          </div>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="poster-card p-5">
            <p className="type-kicker">Equipo</p>
            <h3 className="mt-1 font-display text-2xl uppercase text-ink">Carga por tutor</h3>
            <p className="mt-1 text-xs text-ink/50">Top 10 por clases impartidas en el periodo.</p>
            <div className="mt-4 w-full" style={{ height: Math.max(260, data.carga_tutores.length * 38) }}>
              {data.carga_tutores.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.carga_tutores} layout="vertical" margin={{ top: 4, right: 12, left: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#171313" strokeOpacity={0.1} horizontal={false} />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10, fill: "#171313" }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="tutor" width={128} tick={{ fontSize: 10, fill: "#171313" }} axisLine={false} tickLine={false} />
                    <Tooltip {...CHART_TOOLTIP} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="impartidas" name="Impartidas" fill={COLORS.asistio} maxBarSize={14} />
                    <Bar dataKey="faltas" name="Faltas" fill={COLORS.falta} maxBarSize={14} />
                    <Bar dataKey="cubiertas" name="Cubiertas" fill={COLORS.cubierta} maxBarSize={14} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="grid h-full place-items-center border border-dashed border-ink/20 bg-sand/30 text-sm text-ink/50">Sin carga registrada.</div>
              )}
            </div>
          </div>

          <div className="poster-card p-5">
            <p className="type-kicker">Sedes</p>
            <h3 className="mt-1 font-display text-2xl uppercase text-ink">Asistencia por sede</h3>
            <div className="mt-4 space-y-4">
              {data.asistencia.por_sede.length ? data.asistencia.por_sede.map((sede) => (
                <div key={sede.sede_id}>
                  <div className="flex items-baseline justify-between gap-3">
                    <p className="text-sm font-semibold text-ink">{sede.sede}</p>
                    <p className="font-mono text-xs text-ink/55">{sede.tasa}% · {number(sede.total)} sesiones</p>
                  </div>
                  <div className="mt-1 h-2 border border-ink/15 bg-sand">
                    <div className="h-full bg-accent-deep" style={{ width: `${Math.min(100, sede.tasa)}%` }} />
                  </div>
                  <p className="mt-1 font-mono text-[0.56rem] uppercase tracking-[0.08em] text-ink/40">
                    {sede.faltas} faltas · {sede.cubiertas} cubiertas · {sede.pendientes} pendientes
                  </p>
                </div>
              )) : <p className="text-sm text-ink/50">Sin sesiones por sede en el periodo.</p>}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
