"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, ExternalLink, ReceiptText, Search, X } from "lucide-react";
import { toast } from "sonner";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pagination } from "@/components/ui/pagination";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface Pago {
  id: number;
  student_id: number;
  matricula: string | null;
  student_name: string | null;
  cargo_concepto: string | null;
  monto: number;
  moneda: string;
  metodo: string;
  estado: string;
  referencia: string | null;
  comprobante_nombre: string | null;
  comprobante_url: string | null;
  recibo_codigo: string | null;
  motivo_rechazo: string | null;
  created_at: string;
}

interface Page {
  items: Pago[];
  total: number;
  page: number;
  page_size: number;
}

function money(value: number, currency = "MXN") {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency }).format(value);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export default function PagosPage() {
  const token = useAuthStore((s) => s.token);
  const role = useAuthStore((s) => s.user?.role || "");
  const canValidate = ["admin", "coordinador", "subcoordinador"].includes(role);
  const headers = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token]);
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [estatus, setEstatus] = useState("");
  const [metodo, setMetodo] = useState("");
  const [rejecting, setRejecting] = useState<number | null>(null);
  const [motivo, setMotivo] = useState("");
  const [busy, setBusy] = useState(false);

  const params = useMemo(
    () => ({
      page,
      page_size: 25,
      search: search || undefined,
      estatus: estatus || undefined,
      metodo: metodo || undefined,
    }),
    [page, search, estatus, metodo],
  );

  const { data, isLoading, refetch } = useQuery<Page>({
    queryKey: ["pagos-staff", params],
    queryFn: async () => (await api.get("/pagos", { headers, params })).data,
    enabled: Boolean(token),
  });

  const totalPages = Math.max(1, Math.ceil((data?.total || 0) / (data?.page_size || 25)));

  function applySearch(event: React.FormEvent) {
    event.preventDefault();
    setSearch(searchInput.trim());
    setPage(1);
  }

  function clearFilters() {
    setSearchInput("");
    setSearch("");
    setEstatus("");
    setMetodo("");
    setPage(1);
  }

  async function validate(pago: Pago, aprobado: boolean, reason?: string) {
    setBusy(true);
    try {
      await api.post(
        `/pagos/${pago.id}/validar`,
        { aprobado, motivo: reason || null },
        { headers },
      );
      toast.success(aprobado ? "Pago validado y recibo generado." : "Pago rechazado.");
      setRejecting(null);
      setMotivo("");
      await refetch();
      await queryClient.invalidateQueries({ queryKey: ["aspirantes"] });
    } catch {
      toast.error("No pudimos actualizar el pago.");
    } finally {
      setBusy(false);
    }
  }

  async function openComprobante(pago: Pago) {
    try {
      const response = await api.get(`/pagos/${pago.id}/comprobante`, { headers });
      window.open(response.data.url, "_blank", "noopener,noreferrer");
    } catch {
      toast.error("El comprobante no está disponible. Revisa la configuración de almacenamiento.");
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
      toast.error("El recibo no está disponible.");
    }
  }

  const columns: Column<Pago>[] = [
    {
      key: "recibo",
      header: "Pago",
      sortValue: (item) => item.id,
      render: (item) => (
        <div>
          <p className="font-mono text-xs font-bold text-ink">#{item.id}</p>
          <p className="text-xs text-ink/45">{formatDate(item.created_at)}</p>
        </div>
      ),
    },
    {
      key: "student_name",
      header: "Aspirante",
      sortValue: (item) => item.student_name || "",
      searchValue: (item) => [item.student_name, item.matricula, item.referencia].filter(Boolean).join(" "),
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{item.student_name || `Alumno #${item.student_id}`}</p>
          <p className="font-mono text-xs text-ink/50">{item.matricula || "Sin matrícula"}</p>
        </div>
      ),
    },
    {
      key: "monto",
      header: "Monto",
      sortValue: (item) => item.monto,
      render: (item) => (
        <div>
          <p className="font-semibold text-ink">{money(item.monto, item.moneda)}</p>
          <p className="text-xs capitalize text-ink/45">{item.metodo} · {item.cargo_concepto || "cargo"}</p>
        </div>
      ),
    },
    {
      key: "referencia",
      header: "Referencia",
      render: (item) => (
        <span className="text-xs text-ink/60">{item.referencia || "—"}</span>
      ),
    },
    {
      key: "estado",
      header: "Estado",
      sortValue: (item) => item.estado,
      render: (item) => <StatusBadge status={item.estado} />,
    },
    {
      key: "acciones",
      header: "",
      className: "text-right",
      render: (item) => (
        <div className="flex flex-wrap justify-end gap-1">
          {item.comprobante_nombre ? (
            <Button size="sm" variant="outline" onClick={() => openComprobante(item)}>
              <ExternalLink className="mr-1 h-3.5 w-3.5" /> Comprobante
            </Button>
          ) : null}
          {canValidate && item.estado === "pendiente" ? (
            <>
              <Button size="sm" onClick={() => validate(item, true)} disabled={busy}>
                <Check className="mr-1 h-3.5 w-3.5" /> Validar
              </Button>
              <Button size="sm" variant="destructive" onClick={() => { setRejecting(item.id); setMotivo(""); }}>
                <X className="mr-1 h-3.5 w-3.5" /> Rechazar
              </Button>
            </>
          ) : null}
          {item.estado === "validado" ? (
            <Button size="sm" variant="outline" onClick={() => downloadRecibo(item)}>
              <Download className="mr-1 h-3.5 w-3.5" /> Recibo
            </Button>
          ) : null}
        </div>
      ),
    },
  ];

  return (
    <AppShell title="Pagos">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Validación manual"
          title="Pagos"
          description="Revisa los comprobantes de transferencia, valida abonos y descarga los recibos emitidos."
        />

        <div className="poster-card flex flex-col gap-3 p-4">
          <form onSubmit={applySearch} className="flex flex-1 flex-wrap items-center gap-2">
            <label className="relative min-w-[240px] flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink/40" />
              <Input
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder="Buscar nombre, matrícula, referencia o recibo"
                className="h-10 w-full pl-9"
              />
            </label>
            <Button type="submit" size="sm">Buscar</Button>
            <select
              aria-label="Filtrar por estado"
              className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              value={estatus}
              onChange={(event) => { setEstatus(event.target.value); setPage(1); }}
            >
              <option value="">Estado: todos</option>
              <option value="pendiente">Pendiente</option>
              <option value="validado">Validado</option>
              <option value="rechazado">Rechazado</option>
            </select>
            <select
              aria-label="Filtrar por método"
              className="h-10 border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              value={metodo}
              onChange={(event) => { setMetodo(event.target.value); setPage(1); }}
            >
              <option value="">Método: todos</option>
              <option value="efectivo">Efectivo</option>
              <option value="transferencia">Transferencia</option>
            </select>
            {search || estatus || metodo ? (
              <Button type="button" size="sm" variant="outline" onClick={clearFilters}>
                <X className="mr-1 h-3.5 w-3.5" /> Limpiar
              </Button>
            ) : null}
          </form>
          <p className="font-mono text-[0.62rem] uppercase tracking-[0.08em] text-ink/45">
            {data?.total || 0} pagos registrados
          </p>
        </div>

        {rejecting ? (
          <div className="poster-card border-primary p-4">
            <p className="flex items-center gap-2 font-display text-xl uppercase text-primary">
              <ReceiptText className="h-4 w-4" /> Motivo del rechazo
            </p>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <Input
                value={motivo}
                onChange={(event) => setMotivo(event.target.value)}
                placeholder="Ej. el monto no coincide con el comprobante"
                className="h-10 flex-1"
              />
              <Button
                variant="destructive"
                onClick={() => {
                  const pago = data?.items.find((item) => item.id === rejecting);
                  if (pago) void validate(pago, false, motivo);
                }}
                disabled={busy || !motivo.trim()}
              >
                Confirmar rechazo
              </Button>
              <Button variant="outline" onClick={() => { setRejecting(null); setMotivo(""); }}>
                Cancelar
              </Button>
            </div>
          </div>
        ) : null}

        <DataTable
          columns={columns}
          data={data?.items}
          isLoading={isLoading}
          keyExtractor={(item) => item.id}
          searchable={false}
          emptyMessage="No hay pagos que coincidan con los filtros."
          initialSort={{ key: "recibo", direction: "desc" }}
        />
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </AppShell>
  );
}
