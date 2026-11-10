"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";

interface Assignment { corrida_id: number; grupo_id: number; grupo: string | null; materia: string | null; dia: number; hora_inicio: string; hora_fin: string; }

export default function MiHorarioPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const { data } = useQuery<Assignment[]>({ queryKey: ["mi-horario"], queryFn: async () => (await api.get("/tutores/me/horario", { headers })).data });

  return (
    <AppShell title="Mi horario">
      <div className="space-y-2">
        {(data || []).map((a, i) => (
          <div key={i} className="border border-primary bg-surface rounded-card p-3">
            <p className="font-semibold">{a.materia} — {a.grupo}</p>
            <p className="text-sm">Día {a.dia}: {a.hora_inicio} a {a.hora_fin}</p>
          </div>
        ))}
        {!data?.length && <p className="text-sm text-muted-foreground">No hay horario publicado.</p>}
      </div>
    </AppShell>
  );
}
