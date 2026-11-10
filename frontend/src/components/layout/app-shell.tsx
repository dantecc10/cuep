"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";

const linksByRole: Record<string, { href: string; label: string }[]> = {
  admin: [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/sedes", label: "Sedes" },
    { href: "/dashboard/planes", label: "Planes" },
    { href: "/dashboard/materias", label: "Materias" },
    { href: "/dashboard/usuarios", label: "Usuarios" },
  ],
  coordinador: [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/grupos", label: "Grupos" },
    { href: "/dashboard/tutores", label: "Tutores" },
    { href: "/dashboard/corridas", label: "Corridas" },
    { href: "/dashboard/inscripciones", label: "Inscripciones" },
    { href: "/dashboard/publicar", label: "Publicar" },
  ],
  subcoordinador: [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/grupos", label: "Grupos" },
    { href: "/dashboard/tutores", label: "Tutores" },
    { href: "/dashboard/corridas", label: "Corridas" },
    { href: "/dashboard/inscripciones", label: "Inscripciones" },
    { href: "/dashboard/publicar", label: "Publicar" },
  ],
  tutor: [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/disponibilidad", label: "Disponibilidad" },
    { href: "/dashboard/materias", label: "Materias" },
    { href: "/dashboard/mi-horario", label: "Mi horario" },
  ],
  alumno: [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/mi-inscripcion", label: "Mi inscripción" },
    { href: "/mi-perfil", label: "Mi perfil" },
    { href: "/mi-credencial", label: "Mi credencial" },
    { href: "/mi-horario", label: "Mi horario" },
  ],
};

export function AppShell({ children, title }: { children: React.ReactNode; title?: string }) {
  const router = useRouter();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  useEffect(() => { if (!token) router.push("/login"); }, [token, router]);
  const logout = useAuthStore((s) => s.logout);
  const links = linksByRole[user?.role || ""] || [{ href: "/dashboard", label: "Dashboard" }];

  return (
    <div className="container-site py-8 grid gap-6 md:grid-cols-[220px_1fr]">
      <aside className="bg-surface border border-primary rounded-card p-4 h-fit">
        <p className="font-display text-xl uppercase text-primary">{user?.nombre || "Usuario"}</p>
        <p className="text-xs text-muted-foreground mb-4">{user?.role}</p>
        <nav className="space-y-2">
          {links.map((link) => (
            <Link key={link.href} href={link.href} className="block px-3 py-2 rounded-button hover:bg-paper text-sm font-semibold">
              {link.label}
            </Link>
          ))}
        </nav>
        <Button variant="outline" className="w-full mt-4" onClick={logout}>Cerrar sesión</Button>
      </aside>
      <section className="space-y-6">
        {title && <h1 className="font-display text-4xl uppercase text-primary">{title}</h1>}
        {children}
      </section>
    </div>
  );
}
