"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface HorarioDia {
  dia: number;
  activo: boolean;
  inicio: string;
  fin: string;
}

const DAYS: Record<number, string> = {
  1: "Lunes",
  2: "Martes",
  3: "Miércoles",
  4: "Jueves",
  5: "Viernes",
  6: "Sábado",
  7: "Domingo",
};

export default function HorarioCuepPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery<HorarioDia[]>({
    queryKey: ["horario-cuep"],
    queryFn: async () => (await api.get("/configuracion-horario")).data,
  });
  const [days, setDays] = useState<HorarioDia[]>([]);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (data) setDays(data);
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: async () => api.put("/configuracion-horario", { dias: days }),
    onSuccess: () => {
      setMsg("Horario del CUEP actualizado.");
      queryClient.invalidateQueries({ queryKey: ["horario-cuep"] });
    },
    onError: () => setMsg("No pudimos guardar el horario. Revisa los rangos e inténtalo de nuevo."),
  });

  function updateDay(day: number, patch: Partial<HorarioDia>) {
    setDays((current) => current.map((item) => (item.dia === day ? { ...item, ...patch } : item)));
  }

  function validate() {
    if (!days.some((day) => day.activo)) return "Activa al menos un día.";
    for (const day of days) {
      if (!day.activo) continue;
      if (day.inicio >= day.fin) return `El rango de ${DAYS[day.dia]} no es válido.`;
      if (day.inicio.split(":")[1] !== "00" || day.fin.split(":")[1] !== "00") {
        return "Los horarios deben ser en horas completas.";
      }
    }
    return "";
  }

  function save() {
    const error = validate();
    if (error) {
      setMsg(error);
      return;
    }
    setMsg("");
    saveMutation.mutate();
  }

  return (
    <AppShell title="Horario CUEP">
      <div className="space-y-6">
        <PageHeader
          title="Horario del CUEP"
          description="Define los días y rangos de horas en los que se puede programar el CUEP. Este horario limita la disponibilidad de tutores y el optimizador."
        />

        {isLoading ? (
          <div className="h-64 animate-pulse border border-ink/15 bg-sand" />
        ) : (
          <section className="poster-card p-5 sm:p-6">
            <div className="flex flex-wrap items-end justify-between gap-3 border-b border-ink/15 pb-4">
              <div>
                <p className="type-kicker">Configuración global</p>
                <h2 className="mt-2 font-display text-2xl uppercase text-primary">Días y horas habilitadas</h2>
              </div>
              <p className="max-w-sm text-xs leading-relaxed text-ink/55">
                Los días inactivos no aparecerán para los tutores y no serán considerados por el optimizador.
              </p>
            </div>

            <div className="mt-5 space-y-3">
              {days.map((day) => (
                <div key={day.dia} className={`grid gap-4 border p-4 sm:grid-cols-[1fr_150px_150px] sm:items-end ${day.activo ? "border-ink/25 bg-accent/5" : "border-ink/10 bg-sand/30"}`}>
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-[#A92730]"
                      checked={day.activo}
                      onChange={(event) => updateDay(day.dia, { activo: event.target.checked })}
                    />
                    <span>
                      <span className="block text-sm font-semibold text-ink">{DAYS[day.dia]}</span>
                      <span className="font-mono text-[0.58rem] uppercase tracking-[0.08em] text-ink/45">
                        {day.activo ? "Habilitado" : "Inactivo"}
                      </span>
                    </span>
                  </label>
                  <div className="space-y-1">
                    <Label htmlFor={`inicio-${day.dia}`}>Desde</Label>
                    <Input
                      id={`inicio-${day.dia}`}
                      type="time"
                      step={3600}
                      value={day.inicio}
                      disabled={!day.activo}
                      onChange={(event) => updateDay(day.dia, { inicio: event.target.value })}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor={`fin-${day.dia}`}>Hasta</Label>
                    <Input
                      id={`fin-${day.dia}`}
                      type="time"
                      step={3600}
                      value={day.fin}
                      disabled={!day.activo}
                      onChange={(event) => updateDay(day.dia, { fin: event.target.value })}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-ink/15 pt-5">
              <Button onClick={save} disabled={saveMutation.isPending}>
                {saveMutation.isPending ? "Guardando..." : "Guardar horario"}
              </Button>
              {msg && <p role="status" className="text-sm font-semibold text-accent-deep">{msg}</p>}
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
