"use client";
import { AppShell } from "@/components/layout/app-shell";
interface Group { id: number; materia: string; nombre: string; ocupados: number; capacidad: number; disponibles: number; }
interface Enrollment { id: number; grupo_id: number; estado: string; payment_status: string; }
interface ScheduleItem { grupo_id: number; materia: string; grupo: string; tutor: string | null; horario: { hora_inicio: string; hora_fin: string } | null; }
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function MiInscripcionPage() {
  const [token] = useState(() => (typeof window !== "undefined" ? localStorage.getItem("cuep_token") : null));
  const [groups, setGroups] = useState<Group[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [schedule, setSchedule] = useState<ScheduleItem[]>([]);

  const load = useCallback(async () => {
    const headers = { Authorization: `Bearer ${token}` };
    const [g, e, s] = await Promise.all([
      api.get("/groups/available", { params: { sede_id: 1, nivel: "PREPA" }, headers }),
      api.get("/enrollments/me", { headers }),
      api.get("/students/me/schedule", { headers }),
    ]);
    setGroups(g.data);
    setEnrollments(e.data);
    setSchedule(s.data);
  }, [token]);

  useEffect(() => { load(); }, [load]);

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
      
      <Card>
        <CardHeader><CardTitle>Grupos disponibles</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {groups.map((g) => (
            <div key={g.id} className="flex items-center justify-between border border-primary bg-surface rounded-card p-3">
              <span>{g.materia} — {g.nombre} (cupo {g.ocupados}/{g.capacidad})</span>
              <Button size="sm" onClick={() => enroll(g.id)} disabled={g.disponibles <= 0}>Inscribirme</Button>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Mis inscripciones</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {enrollments.map((e) => (
            <div key={e.id} className="flex items-center justify-between border border-primary bg-surface rounded-card p-3">
              <span>Grupo {e.grupo_id} — {e.estado} ({e.payment_status})</span>
              {e.estado !== "cancelada" && <Button size="sm" variant="outline" onClick={() => cancel(e.id)}>Cancelar</Button>}
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Mi horario</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {schedule.map((s) => (
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
