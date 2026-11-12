"use client";

import { useEffect, useRef, useState } from "react";
import { Download, FileSpreadsheet, Upload } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type ImportEntity = "materias" | "planes" | "sedes" | "usuarios";

interface ImportRowIssue {
  fila: number;
  mensaje: string;
}

interface ImportCreatedRelated {
  tipo: string;
  nombre: string;
  detalle?: string | null;
}

interface ImportCredential {
  email: string;
  password_temporal: string;
  email_enviado: boolean;
}

interface ImportReport {
  entidad: string;
  total: number;
  creadas: number;
  omitidas: number;
  fallidas: number;
  errores: ImportRowIssue[];
  advertencias: ImportRowIssue[];
  creadas_relacionadas: ImportCreatedRelated[];
  credenciales: ImportCredential[];
  correos_enviados: number;
  correos_fallidos: number;
}

const entityCopy: Record<ImportEntity, { title: string; columns: string }> = {
  materias: {
    title: "Importar materias",
    columns: "Columnas: nombre, nivel, area, descripcion. El nivel debe ser PREPA o LICENCIATURA.",
  },
  planes: {
    title: "Importar planes de estudio",
    columns:
      "Columnas: nombre, nivel, area, descripcion, materias. Separa las materias con punto y coma (;). Las materias faltantes se crean automáticamente y se reportan al final.",
  },
  sedes: {
    title: "Importar sedes",
    columns:
      "Columnas: nombre, ciudad, codigo, descripcion, maps_url, image_url, activo. Si el código se deja vacío, se asigna la primera letra disponible y se muestra una advertencia.",
  },
  usuarios: {
    title: "Importar usuarios",
    columns:
      "Columnas: email, nombre, apellido_paterno, apellido_materno, role, sede_codigo, es_tutor, telefono, area_principal, carga_max_horas. Admin puede importar admin, coordinador y tutor; coordinación solo tutores de su sede. Se genera una contraseña temporal y se envía por correo.",
  },
};

function escapeCsv(value: string | number | boolean): string {
  const text = String(value);
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export function ImportDialog({
  entidad,
  open,
  onOpenChange,
  onImported,
}: {
  entidad: ImportEntity;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImported?: () => void;
}) {
  const token = useAuthStore((state) => state.token);
  const headers = { Authorization: `Bearer ${token}` };
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [report, setReport] = useState<ImportReport | null>(null);

  const copy = entityCopy[entidad];

  useEffect(() => {
    if (!open) {
      setFile(null);
      setReport(null);
      setUploading(false);
    }
  }, [open]);

  async function downloadTemplate() {
    setDownloading(true);
    try {
      const response = await api.get(`/imports/${entidad}/template`, {
        headers,
        responseType: "blob",
      });
      downloadBlob(response.data as Blob, `plantilla-${entidad}.csv`);
    } catch {
      toast.error("No se pudo descargar la plantilla.");
    } finally {
      setDownloading(false);
    }
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    const data = new FormData();
    data.append("file", file);
    try {
      const response = await api.post<ImportReport>(`/imports/${entidad}`, data, {
        headers,
        timeout: 600000,
      });
      setReport(response.data);
      onImported?.();
      if (response.data.creadas > 0) {
        toast.success(`${response.data.creadas} registro(s) importado(s).`);
      }
    } catch (error) {
      const detail =
        typeof error === "object" &&
        error !== null &&
        "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      toast.error(detail || "No se pudo importar el CSV.");
    } finally {
      setUploading(false);
    }
  }

  function downloadCredentials() {
    if (!report || report.credenciales.length === 0) return;
    const lines = [
      ["email", "password_temporal", "email_enviado"],
      ...report.credenciales.map((item) => [
        item.email,
        item.password_temporal,
        item.email_enviado ? "si" : "no",
      ]),
    ];
    const csv = "\ufeff" + lines.map((line) => line.map(escapeCsv).join(",")).join("\n");
    downloadBlob(new Blob([csv], { type: "text/csv;charset=utf-8" }), `credenciales-${entidad}.csv`);
  }

  function reset() {
    setFile(null);
    setReport(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange} className="max-w-3xl">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{copy.title}</DialogTitle>
          <DialogDescription>{copy.columns}</DialogDescription>
        </DialogHeader>

        {!report ? (
          <div className="space-y-4">
            <div className="border border-dashed border-ink/30 bg-sand/40 p-5">
              <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <FileSpreadsheet className="mt-0.5 h-8 w-8 text-accent-deep" aria-hidden="true" />
                  <div>
                    <p className="font-semibold text-ink">Archivo CSV</p>
                    <p className="text-xs text-ink/55">
                      Máximo 5 MB y 1000 filas. Los duplicados se omiten y se reportan.
                    </p>
                    {file && <p className="mt-1 text-xs font-semibold text-accent-deep">{file.name}</p>}
                  </div>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <Upload className="h-3.5 w-3.5" aria-hidden="true" />
                  Elegir archivo
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,text/csv"
                  className="sr-only"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2">
              <Button type="button" variant="ghost" onClick={downloadTemplate} disabled={downloading}>
                <Download className="h-3.5 w-3.5" aria-hidden="true" />
                {downloading ? "Descargando..." : "Descargar plantilla"}
              </Button>
              <Button type="button" onClick={handleUpload} disabled={!file || uploading}>
                {uploading ? "Importando..." : "Importar CSV"}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Summary label="Total" value={report.total} />
              <Summary label="Creadas" value={report.creadas} tone="ok" />
              <Summary label="Omitidas" value={report.omitidas} tone="muted" />
              <Summary label="Fallidas" value={report.fallidas} tone={report.fallidas > 0 ? "error" : "muted"} />
            </div>

            {report.advertencias.length > 0 && (
              <section className="border border-yellow bg-yellow/20 p-3">
                <h3 className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-ink">
                  Advertencias
                </h3>
                <ul className="mt-2 space-y-1 text-xs text-ink/75">
                  {report.advertencias.map((item, index) => (
                    <li key={`warning-${index}`}>Fila {item.fila}: {item.mensaje}</li>
                  ))}
                </ul>
              </section>
            )}

            {report.creadas_relacionadas.length > 0 && (
              <section className="border border-accent bg-accent-soft/60 p-3">
                <h3 className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-accent-deep">
                  Registros relacionados creados
                </h3>
                <ul className="mt-2 space-y-1 text-xs text-ink/75">
                  {report.creadas_relacionadas.map((item, index) => (
                    <li key={`related-${index}`}>
                      <span className="font-semibold text-ink">{item.nombre}</span> ({item.tipo})
                      {item.detalle ? ` · ${item.detalle}` : ""}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {report.errores.length > 0 && (
              <section className="border border-primary/40 bg-primary/5 p-3">
                <h3 className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-primary">
                  Filas con error
                </h3>
                <ul className="mt-2 max-h-48 space-y-1 overflow-auto pr-1 text-xs text-ink/75">
                  {report.errores.map((item, index) => (
                    <li key={`error-${index}`}>Fila {item.fila}: {item.mensaje}</li>
                  ))}
                </ul>
              </section>
            )}

            {report.credenciales.length > 0 && (
              <section className="border border-ink/20 bg-surface p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-ink">
                      Contraseñas temporales
                    </h3>
                    <p className="mt-1 text-xs text-ink/55">
                      Se enviaron por correo ({report.correos_enviados} enviados, {report.correos_fallidos} fallidos).
                      Guárdalas ahora: no se volverán a mostrar.
                    </p>
                  </div>
                  <Button type="button" size="sm" variant="outline" onClick={downloadCredentials}>
                    <Download className="h-3.5 w-3.5" aria-hidden="true" />
                    Descargar CSV
                  </Button>
                </div>
                <div className="mt-3 max-h-48 overflow-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-ink/15 text-left font-mono uppercase tracking-[0.08em] text-ink/50">
                        <th className="py-1 pr-2">Email</th>
                        <th className="py-1 pr-2">Contraseña temporal</th>
                        <th className="py-1">Correo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.credenciales.map((item) => (
                        <tr key={item.email} className="border-b border-ink/10">
                          <td className="py-1.5 pr-2">{item.email}</td>
                          <td className="py-1.5 pr-2 font-mono">{item.password_temporal}</td>
                          <td className="py-1.5">
                            <button
                              type="button"
                              className="font-mono text-[0.6rem] font-bold uppercase tracking-[0.08em] text-accent-deep underline"
                              onClick={() => {
                                navigator.clipboard.writeText(item.password_temporal);
                                toast.success("Contraseña copiada.");
                              }}
                            >
                              Copiar
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={reset}>
                Importar otro archivo
              </Button>
              <Button type="button" onClick={() => onOpenChange(false)}>
                Cerrar
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function Summary({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number;
  tone?: "default" | "ok" | "muted" | "error";
}) {
  const toneClass =
    tone === "ok"
      ? "text-accent-deep"
      : tone === "error"
        ? "text-primary"
        : tone === "muted"
          ? "text-ink/50"
          : "text-ink";
  return (
    <div className="border border-ink/15 bg-sand/40 p-3">
      <p className="font-mono text-[0.58rem] uppercase tracking-[0.1em] text-ink/45">{label}</p>
      <p className={`mt-1 font-display text-2xl ${toneClass}`}>{value}</p>
    </div>
  );
}
