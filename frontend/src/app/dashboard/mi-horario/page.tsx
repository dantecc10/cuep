"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { EmptyState } from "@/components/ui/empty-state";

interface Assignment { corrida_id: number; grupo_id: number; grupo: string | null; materia: string | null; dia: number; hora_inicio: string; hora_fin: string; }

const dias: Record<number, string> = { 1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo" };

export default function MiHorarioPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const { data, isLoading } = useQuery<Assignment[]>({ queryKey: ["mi-horario"], queryFn: async () => (await api.get("/tutores/me/horario", { headers })).data });

  const columns: Column<Assignment>[] = [
    { key: "materia", header: "Materia", render: (item) => <span className="font-semibold text-ink">{item.materia || "Sin materia"}</span> },
    { key: "grupo", header: "Grupo", render: (item) => item.grupo || `Grupo ${item.grupo_id}` },
    { key: "dia", header: "Día", render: (item) => dias[item.dia] || `Día ${item.dia}` },
    { key: "horario", header: "Horario", render: (item) => <span className="font-mono text-xs">{item.hora_inicio} — {item.hora_fin}</span> },
  ];

  return (
    <AppShell title="Mi horario">
      <div className="space-y-6">
        <PageHeader title="Mi horario" description="Asesorías que te fueron asignadas en la última publicación." />
        {!isLoading && (!data || data.length === 0) ? (
          <EmptyState title="Sin horario publicado" description="Cuando coordinación publique los horarios, tus asesorías aparecerán aquí." />
        ) : (
          <DataTable columns={columns} data={data} isLoading={isLoading} keyExtractor={(item) => `${item.corrida_id}-${item.grupo_id}-${item.dia}-${item.hora_inicio}`} />
        )}
      </div>
    </AppShell>
  );
}
