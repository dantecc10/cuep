"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Group { id: number; materia: string; nombre: string; ocupados: number; capacidad: number; disponibles: number; }
interface Enrollment {
  id: number;
  grupo_id: number;
  estado: string;
  payment_status: string;
  grupo_name: string | null;
  materia_name: string | null;
}
interface Student { sede_id: number | null; nivel: string; area: string | null; }
interface ScheduleItem { grupo_id: number; materia: string; grupo: string; tutor: string | null; horario: { hora_inicio: string; hora_fin: string } | null; }

export default function MiInscripcionPage() {
  const token = useAuthStore((s) => s.token);
  const [groups, setGroups] = useState<Group[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);
  const [error, setError] = useState("");
  const [groupSearch, setGroupSearch] = useState("");
  const [groupSort, setGroupSort] = useState("materia-asc");
  const [onlyAvailable, setOnlyAvailable] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setError("");
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const meResponse = await api.get<Student>("/students/me", { headers });
      const student = meResponse.data;
      const groupsRequest = student.sede_id
        ? api.get<Group[]>("/groups/available", {
            headers,
            params: {
              sede_id: student.sede_id,
              nivel: student.nivel,
              area: student.area || undefined,
            },
          })
        : Promise.resolve({ data: [] as Group[] });
      const [g, e, s] = await Promise.all([
        groupsRequest,
        api.get<Enrollment[]>("/enrollments/me", { headers }),
        api.get<ScheduleItem[]>("/students/me/schedule", { headers }),
      ]);
      setGroups(g.data);
      setEnrollments(e.data);
      setSchedule(s.data);
    } catch {
      setError("No pudimos cargar tu inscripción. Revisa tu conexión e inténtalo de nuevo.");
    }
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const filteredGroups = useMemo(() => {
    const term = groupSearch.trim().toLocaleLowerCase("es");
    const list = groups.filter((group) => {
      if (onlyAvailable && group.disponibles <= 0) return false;
      if (!term) return true;
      return [group.materia, group.nombre]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("es")
        .includes(term);
    });
    return [...list].sort((a, b) => {
      if (groupSort === "nombre-asc") return a.nombre.localeCompare(b.nombre, "es");
      if (groupSort === "cupo-desc") return b.disponibles - a.disponibles || a.nombre.localeCompare(b.nombre, "es");
      return a.materia.localeCompare(b.materia, "es") || a.nombre.localeCompare(b.nombre, "es");
    });
  }, [groups, groupSearch, groupSort, onlyAvailable]);

  async function enroll(grupoId: number) {
    const headers = { Authorization: `Bearer ${token}` };
    await api.post("/enrollments", { grupo_id: grupoId }, { headers });
    await load();
  }

  async function cancel(id: number) {
    const headers = { Authorization: `Bearer ${token}` };
    await api.delete(`/enrollments/${id}`, { headers });
    await load();
  }

  return (
    <AppShell title="Mi inscripción">
      <div className="space-y-6">
        <PageHeader title="Mi inscripción" description="Elige tus grupos, revisa tu estado de pago y consulta tu horario." />

        {error && (
          <div className="poster-card flex flex-wrap items-center justify-between gap-3 p-4">
            <p className="text-sm font-semibold text-primary">{error}</p>
            <Button size="sm" variant="outline" onClick={load}>Reintentar</Button>
          </div>
        )}

        <Card>
          <CardHeader><CardTitle>Grupos disponibles</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <input
                value={groupSearch}
                onChange={(event) => setGroupSearch(event.target.value)}
                placeholder="Buscar materia o grupo..."
                aria-label="Buscar grupo disponible"
                className="h-10 flex-1 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
              />
              <select
                aria-label="Ordenar grupos"
                className="h-10 border border-ink/25 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                value={groupSort}
                onChange={(event) => setGroupSort(event.target.value)}
              >
                <option value="materia-asc">Materia A-Z</option>
                <option value="nombre-asc">Grupo A-Z</option>
                <option value="cupo-desc">Más cupo</option>
              </select>
              <label className="flex items-center gap-2 text-xs text-ink/60">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-[#A92730]"
                  checked={onlyAvailable}
                  onChange={(event) => setOnlyAvailable(event.target.checked)}
                />
                Solo con cupo
              </label>
            </div>
            {groups.length === 0 ? (
              <p className="text-sm text-ink/55">Aún no hay grupos disponibles para tu sede y nivel.</p>
            ) : filteredGroups.length === 0 ? (
              <p className="border border-dashed border-ink/20 bg-sand/30 px-3 py-4 text-xs text-ink/55">
                No hay grupos que coincidan con la búsqueda.
              </p>
            ) : filteredGroups.map((g) => (
              <div key={g.id} className="flex flex-wrap items-center justify-between gap-2 border border-primary bg-surface rounded-card p-3">
                <span>{g.materia} — {g.nombre} (cupo {g.ocupados}/{g.capacidad})</span>
                <Button size="sm" onClick={() => enroll(g.id)} disabled={g.disponibles <= 0}>Inscribirme</Button>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Mis inscripciones</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {enrollments.length === 0 ? (
              <p className="text-sm text-ink/55">Todavía no tienes inscripciones.</p>
            ) : enrollments.map((e) => (
              <div key={e.id} className="flex items-center justify-between border border-primary bg-surface rounded-card p-3">
                <div>
                  <p className="font-semibold text-ink">{e.materia_name || "Materia"} · {e.grupo_name || `Grupo ${e.grupo_id}`}</p>
                  <p className="text-xs text-ink/55">{e.estado} ({e.payment_status})</p>
                </div>
                {e.estado !== "cancelada" && <Button size="sm" variant="outline" onClick={() => cancel(e.id)}>Cancelar</Button>}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Mi horario</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {schedule.length === 0 ? (
              <p className="text-sm text-ink/55">Tu horario aparecerá cuando se publiquen las corridas.</p>
            ) : schedule.map((s) => (
              <div key={s.grupo_id} className="border border-primary bg-surface rounded-card p-3">
                {s.materia} — {s.grupo} | Tutor: {s.tutor || "pendiente"} | {s.horario ? `${s.horario.hora_inicio} - ${s.horario.hora_fin}` : "sin horario"}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
