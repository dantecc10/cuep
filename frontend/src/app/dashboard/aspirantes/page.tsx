"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, Eye, FileDown, Search, X } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Sede {
  id: number;
  nombre: string;
}

interface Config {
  anio: number;
}

interface Aspirante {
  id: number;
  matricula: string | null;
  folio: number | null;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  nivel: string;
  area: string | null;
  sede_id: number | null;
  estatus: string;
  anio: number;
  checkin_at: string | null;
  created_at: string;
}

interface Page {
  items: Aspirante[];
  total: number;
  page: number;
  page_size: number;
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
  created_at: string;
}

interface Evento {
  id: number;
  tipo: string;
  estado_anterior: string | null;
  estado_nuevo: string | null;
  created_at: string;
}

interface Detalle extends Aspirante {
  address: string | null;
  colony: string | null;
  municipality_state: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  high_school_type: string | null;
  exam_attempts: string | null;
  desired_degree: string | null;
  study_area: string | null;
  notes: string | null;
  cargos: Cargo[];
  pagos: Pago[];
  eventos: Evento[];
  saldo: number;
}

const ESTATUS = [
  "registrado",
  "en_inscripcion",
  "inscrito",
  "activo",
  "no_asistio",
  "cancelado",
  "baja",
];

const AREAS = [
  "Ingeniería y Ciencias Exactas",
  "Ciencias Sociales",
  "Ciencias Naturales y de la Salud",
];

function formatDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export default function AspirantesPage() {
  const token = useAuthStore((s) => s.token);
  const role = useAuthStore((s) => s.user?.role || "");
  const canEdit = ["admin", "coordinador", "subcoordinador"].includes(role);
  const canExport = canEdit;
  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [estatus, setEstatus] = useState("");
  const [sedeId, setSedeId] = useState("");
  const [nivel, setNivel] = useState("");
  const [area, setArea] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const { data: config } = useQuery<Config>({
    queryKey: ["inscripcion-config"],
    queryFn: async () => (await api.get("/inscripciones/config")).data,
  });
  const { data: sedes } = useQuery<Sede[]>({
    queryKey: ["sedes"],
    queryFn: async () => (await api.get("/sedes")).data,
  });

  const params = useMemo(
    () => ({
      page,
      page_size: 25,
      anio: config?.anio,
      search: search || undefined,
      estatus: estatus || undefined,
      sede_id: sedeId || undefined,
      nivel: nivel || undefined,
      area: area || undefined,
    }),
    [page, config?.anio, search, estatus, sedeId, nivel, area],
  );

  const { data, isLoading, refetch } = useQuery<Page>({
    queryKey: ["aspirantes", params],
    queryFn: async () => (await api.get("/inscripciones", { headers, params })).data,
    enabled: Boolean(token && config?.anio),
  });

  const { data: detalle, isLoading: detailLoading } = useQuery<Detalle>({
    queryKey: ["aspirante", selectedId],
    queryFn: async () => (await api.get(`/inscripciones/${selectedId}`, { headers })).data,
    enabled: Boolean(token && selectedId),
  });

  const sedeNames = useMemo(
    () => new Map((sedes || []).map((sede) => [sede.id, sede.nombre])),
    [sedes],
  );
  const totalPages = Math.max(1, Math.ceil((data?.total || 0) / (data?.page_size || 25)));
  const activeFilters = Boolean(search || estatus || sedeId || nivel || area);

  function clearFilters() {
    setSearchInput("");
    setSearch("");
    setEstatus("");
    setSedeId("");
    setNivel("");
    setArea("");
    setPage(1);
  }

  function applySearch(event: React.FormEvent) {
    event.preventDefault();
    setSearch(searchInput.trim());
    setPage(1);
  }

  async function changeEstatus(studentId: number, nextEstatus: string) {
    setSaving(true);
    try {
      await api.patch(`/inscripciones/${studentId}/estatus`, { estatus: nextEstatus }, { headers });
      toast.success("Estatus actualizado.");
      await refetch();
    } catch {
      toast.error("No pudimos cambiar el estatus.");
    } finally {
      setSaving(false);
    }
  }

  async function downloadPase(studentId: number) {
    try {
      const response = await api.get(`/inscripciones/${studentId}/pase`, {
        headers,
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `pase-${studentId}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("No pudimos descargar el pase.");
    }
  }

  async function exportCsv() {
    try {
      const response = await api.get("/inscripciones/export.csv", {
        headers,
        params,
        responseType: "blob",
      });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = `inscripciones-${config?.anio || "todas"}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("No pudimos exportar el padrón.");
    }
  }

  const columns: Column<Aspirante>[] = [
    {
      key: "matricula",
      header: "Matrícula",
      sortValue: (item) => item.matricula || "",
      render: (item) => (
        <span className="font-mono text-xs font-bold text-ink">
          {item.matricula || `#${item.id}`}
        </span>
      ),
    },
    {
      key: "full_name",
      header: "Aspirante",
      sortValue: (item) => item.full_name || "",
      searchValue: (item) => [item.full_name, item.email, item.phone].filter(Boolean).join(" "),
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.full_name || "Sin nombre"}</p>
          <p className="text-xs text-ink/50">{item.email || "Sin correo"}</p>
        </div>
      ),
    },
    {
      key: "sede",
      header: "Sede",
      sortValue: (item) => (item.sede_id ? sedeNames.get(item.sede_id) || "" : ""),
      render: (item) => (
        <span className="text-xs text-ink/65">
          {item.sede_id ? sedeNames.get(item.sede_id) || `Sede #${item.sede_id}` : "—"}
        </span>
      ),
    },
    {
      key: "nivel",
      header: "Nivel / área",
      sortValue: (item) => item.nivel,
      render: (item) => (
        <div>
          <p className="text-xs font-semibold uppercase text-ink/70">{item.nivel}</p>
          <p className="text-xs text-ink/45">{item.area || "Sin área"}</p>
        </div>
      ),
    },
    {
      key: "estatus",
      header: "Estatus",
      sortValue: (item) => item.estatus,
      render: (item) => <StatusBadge status={item.estatus} />,
    },
    {
      key: "checkin_at",
      header: "Check-in",
      sortValue: (item) => item.checkin_at || "",
      render: (item) => (
        <span className="text-xs text-ink/60">{item.checkin_at ? formatDate(item.checkin_at) : "Pendiente"}</span>
      ),
    },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <div className="flex justify-end gap-1">
          <Button size="sm" variant="outline" onClick={() => setSelectedId(item.id)}>
            <Eye className="h-3.5 w-3.5" />
          </Button>
          <Button size="sm" variant="outline" onClick={() => downloadPase(item.id)}>
            <Download className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <AppShell title="Aspirantes">
      <div className="space-y-6">
        <PageHeader
          eyebrow={`Padrón ${config?.anio || ""}`}
          title="Aspirantes"
          description="Consulta el padrón anual, valida matrículas y da seguimiento al proceso de inscripción."
          actions={
            canExport ? (
              <Button variant="outline" onClick={exportCsv}>
                <FileDown className="mr-2 h-4 w-4" /> Exportar CSV
              </Button>
            ) : undefined
          }
        />

        <div className="poster-card flex flex-col gap-3 p-4">
          <form onSubmit={applySearch} className="flex flex-1 flex-wrap items-center gap-2">
            <label className="relative min-w-[240px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/40" />
              <Input
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="Buscar nombre, matrícula, correo o teléfono"
                className="h-10 w-full pl-9"
              />
            </label>
            <Button type="submit" size="sm">Buscar</Button>
            <select
              aria-label="Filtrar por estatus"
              className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              value={estatus}
              onChange={(event) => { setEstatus(event.target.value); setPage(1); }}
            >
              <option value="">Estatus: todos</option>
              {ESTATUS.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
            </select>
            <select
              aria-label="Filtrar por nivel"
              className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              value={nivel}
              onChange={(event) => { setNivel(event.target.value); setPage(1); }}
            >
              <option value="">Nivel: todos</option>
              <option value="PREPA">Preparatoria</option>
              <option value="LICENCIATURA">Licenciatura</option>
            </select>
            <select
              aria-label="Filtrar por área"
              className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              value={area}
              onChange={(event) => { setArea(event.target.value); setPage(1); }}
            >
              <option value="">Área: todas</option>
              {AREAS.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
            {role === "admin" ? (
              <select
                aria-label="Filtrar por sede"
                className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={sedeId}
                onChange={(event) => { setSedeId(event.target.value); setPage(1); }}
              >
                <option value="">Sede: todas</option>
                {(sedes || []).map((sede) => <option key={sede.id} value={sede.id}>{sede.nombre}</option>)}
              </select>
            ) : null}
            {activeFilters ? (
              <Button type="button" variant="outline" size="sm" onClick={clearFilters}>
                <X className="mr-1 h-3.5 w-3.5" /> Limpiar
              </Button>
            ) : null}
          </form>
          <p className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/45">
            {data?.total || 0} registros en {config?.anio || "el ciclo"}
          </p>
        </div>

        <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
          <div className="space-y-3">
            <DataTable
              columns={columns}
              data={data?.items}
              isLoading={isLoading}
              keyExtractor={(item) => item.id}
              searchable={false}
              emptyMessage="No hay aspirantes que coincidan con los filtros."
              initialSort={{ key: "matricula", direction: "asc" }}
            />
            <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
          </div>

          <div className="space-y-4">
            {selectedId ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between gap-2">
                    <span>Detalle</span>
                    <Button size="sm" variant="ghost" onClick={() => setSelectedId(null)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                  {detailLoading || !detalle ? (
                    <div className="h-40 animate-pulse bg-ink/10" />
                  ) : (
                    <>
                      <div>
                        <p className="font-display text-2xl uppercase leading-none text-ink">
                          {detalle.full_name}
                        </p>
                        <p className="mt-1 font-mono text-xs font-bold text-primary">
                          {detalle.matricula}
                        </p>
                        <div className="mt-2"><StatusBadge status={detalle.estatus} /></div>
                      </div>
                      <dl className="space-y-1.5 text-xs text-ink/65">
                        <div><dt className="font-semibold text-ink">Correo</dt><dd>{detalle.email || "—"}</dd></div>
                        <div><dt className="font-semibold text-ink">Teléfono</dt><dd>{detalle.phone || "—"}</dd></div>
                        <div><dt className="font-semibold text-ink">Sede</dt><dd>{detalle.sede_id ? sedeNames.get(detalle.sede_id) || `Sede #${detalle.sede_id}` : "—"}</dd></div>
                        <div><dt className="font-semibold text-ink">Dirección</dt><dd>{[detalle.address, detalle.colony, detalle.municipality_state].filter(Boolean).join(", ") || "—"}</dd></div>
                        <div><dt className="font-semibold text-ink">Emergencia</dt><dd>{[detalle.emergency_contact_name, detalle.emergency_contact_phone].filter(Boolean).join(" · ") || "—"}</dd></div>
                        <div><dt className="font-semibold text-ink">Bachillerato</dt><dd>{detalle.high_school_type || "—"}</dd></div>
                        <div><dt className="font-semibold text-ink">Carrera deseada</dt><dd>{detalle.desired_degree || "—"}</dd></div>
                        <div><dt className="font-semibold text-ink">Check-in</dt><dd>{formatDate(detalle.checkin_at)}</dd></div>
                      </dl>

                      {canEdit ? (
                        <div className="space-y-1.5">
                          <p className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.08em] text-ink/50">Cambiar estatus</p>
                          <select
                            className="h-9 w-full border border-ink/30 bg-surface px-2 text-sm text-ink outline-none focus-visible:border-primary"
                            value={detalle.estatus}
                            onChange={(event) => changeEstatus(detalle.id, event.target.value)}
                            disabled={saving}
                          >
                            {ESTATUS.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
                          </select>
                        </div>
                      ) : null}

                      <div>
                        <p className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.08em] text-ink/50">
                          Cargos · saldo ${detalle.saldo.toFixed(2)}
                        </p>
                        {detalle.cargos.length === 0 ? (
                          <p className="mt-1 text-xs text-ink/50">Sin cargos.</p>
                        ) : detalle.cargos.map((cargo) => (
                          <div key={cargo.id} className="mt-2 flex items-center justify-between gap-2 text-xs">
                            <span className="capitalize">{cargo.concepto} · ${Number(cargo.monto).toFixed(2)}</span>
                            <StatusBadge status={cargo.estado} />
                          </div>
                        ))}
                      </div>

                      <div>
                        <p className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.08em] text-ink/50">Últimos eventos</p>
                        {detalle.eventos.slice(0, 5).map((evento) => (
                          <p key={evento.id} className="mt-1 text-xs text-ink/55">
                            {evento.tipo.replaceAll("_", " ")} · {formatDate(evento.created_at)}
                          </p>
                        ))}
                      </div>

                      <Button className="w-full" variant="outline" onClick={() => downloadPase(detalle.id)}>
                        <Download className="mr-2 h-4 w-4" /> Descargar pase
                      </Button>
                    </>
                  )}
                </CardContent>
              </Card>
            ) : (
              <div className="border border-dashed border-ink/25 bg-surface px-4 py-10 text-center">
                <p className="font-editorial text-base text-ink/55">
                  Selecciona un aspirante para ver su detalle, cargos y eventos.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
