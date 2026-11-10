"use client";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { SectionHeading } from "@/components/layout/section-heading";

export default function DashboardPage() {
  const logout = useAuthStore((s) => s.logout);
  return (
    <div className="container-site py-10 space-y-6">
      <SectionHeading eyebrow="Panel operativo" title="Dashboard CUEP" description="Gestiona tutores, grupos, corridas e inscripciones." />
      <div className="grid gap-4 md:grid-cols-3">
        <article className="bg-surface border border-primary rounded-card p-5 poster-shadow">
          <h3 className="font-display text-2xl uppercase text-primary">Tutores</h3>
          <p className="mt-2 text-sm">Disponibilidad y materias habilitadas.</p>
        </article>
        <article className="bg-surface border border-primary rounded-card p-5">
          <h3 className="font-display text-2xl uppercase text-primary">Corridas</h3>
          <p className="mt-2 text-sm">Solicita y consulta generaciones de horarios.</p>
        </article>
        <article className="bg-surface border border-primary rounded-card p-5">
          <h3 className="font-display text-2xl uppercase text-primary">Inscripciones</h3>
          <p className="mt-2 text-sm">Cupos, lista de espera y asignación.</p>
        </article>
      </div>
      <Button onClick={logout} variant="outline">Cerrar sesión</Button>
    </div>
  );
}
