"use client";
import { AppShell } from "@/components/layout/app-shell";

export default function DashboardPage() {
  return (
    <AppShell title="Dashboard CUEP">
      <div className="grid gap-4 md:grid-cols-3">
        <article className="bg-surface border border-primary rounded-card p-5 poster-shadow">
          <h2 className="font-display text-2xl uppercase text-primary">Tutores</h2>
          <p className="mt-2 text-sm">Disponibilidad y materias habilitadas.</p>
        </article>
        <article className="bg-surface border border-primary rounded-card p-5">
          <h2 className="font-display text-2xl uppercase text-primary">Corridas</h2>
          <p className="mt-2 text-sm">Solicita y consulta generaciones de horarios.</p>
        </article>
        <article className="bg-surface border border-primary rounded-card p-5">
          <h2 className="font-display text-2xl uppercase text-primary">Inscripciones</h2>
          <p className="mt-2 text-sm">Cupos, lista de espera y asignación.</p>
        </article>
      </div>
    </AppShell>
  );
}
