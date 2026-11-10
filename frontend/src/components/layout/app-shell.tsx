"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  BadgeCheck,
  BookOpen,
  CalendarClock,
  CalendarDays,
  ClipboardList,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Layers,
  LogOut,
  MapPin,
  PlayCircle,
  Send,
  Users,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { useAuthStore } from "@/store/auth";

type NavLink = { href: string; label: string; icon: LucideIcon };

const linksByRole: Record<string, NavLink[]> = {
  admin: [
    { href: "/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/dashboard/sedes", label: "Sedes", icon: MapPin },
    { href: "/dashboard/planes", label: "Planes", icon: Layers },
    { href: "/dashboard/materias", label: "Materias", icon: BookOpen },
    { href: "/dashboard/usuarios", label: "Usuarios", icon: Users },
  ],
  coordinador: [
    { href: "/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/dashboard/grupos", label: "Grupos", icon: Users },
    { href: "/dashboard/tutores", label: "Tutores", icon: GraduationCap },
    { href: "/dashboard/corridas", label: "Corridas", icon: PlayCircle },
    { href: "/dashboard/inscripciones", label: "Inscripciones", icon: ClipboardList },
    { href: "/dashboard/publicar", label: "Publicar", icon: Send },
  ],
  subcoordinador: [
    { href: "/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/dashboard/grupos", label: "Grupos", icon: Users },
    { href: "/dashboard/tutores", label: "Tutores", icon: GraduationCap },
    { href: "/dashboard/corridas", label: "Corridas", icon: PlayCircle },
    { href: "/dashboard/inscripciones", label: "Inscripciones", icon: ClipboardList },
    { href: "/dashboard/publicar", label: "Publicar", icon: Send },
  ],
  tutor: [
    { href: "/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/dashboard/disponibilidad", label: "Disponibilidad", icon: CalendarClock },
    { href: "/dashboard/materias", label: "Materias", icon: BookOpen },
    { href: "/dashboard/mi-horario", label: "Mi horario", icon: CalendarDays },
  ],
  alumno: [
    { href: "/dashboard", label: "Panel", icon: LayoutDashboard },
    { href: "/mi-inscripcion", label: "Mi inscripción", icon: FileText },
    { href: "/mi-perfil", label: "Mi perfil", icon: UserRound },
    { href: "/mi-credencial", label: "Mi credencial", icon: BadgeCheck },
    { href: "/mi-horario", label: "Mi horario", icon: CalendarDays },
  ],
};

const roleLabels: Record<string, string> = {
  admin: "Administración",
  coordinador: "Coordinación",
  subcoordinador: "Subcoordinación",
  tutor: "Tutoría",
  alumno: "Estudiante",
};

export function AppShell({ children, title }: { children: React.ReactNode; title?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    if (!token) router.push("/login");
  }, [token, router]);

  const links = linksByRole[user?.role || ""] || [{ href: "/dashboard", label: "Panel", icon: LayoutDashboard }];
  const activeLink = links.find((link) => link.href === pathname);
  const displayTitle = title || activeLink?.label || "Panel";
  const initials = `${user?.nombre?.[0] || "C"}${user?.apellido_paterno?.[0] || "U"}`.toUpperCase();

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <div className="min-h-screen bg-cream text-ink">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[276px] flex-col border-r-[1.5px] border-ink bg-ink text-paper-light md:flex">
        <div className="border-b border-paper-light/15 p-5">
          <Link href="/dashboard" className="group flex items-center gap-3">
            <span className="grid h-12 w-12 -rotate-3 place-items-center border-[1.5px] border-yellow bg-primary shadow-[3px_3px_0_#E8B83E] transition-transform group-hover:rotate-0">
              <Image src="/identity/heart.png" alt="" width={30} height={30} className="h-7 w-7" />
            </span>
            <span>
              <span className="block font-display text-3xl uppercase leading-none text-yellow">CUEP</span>
              <span className="mt-1 block font-mono text-[0.55rem] uppercase tracking-[0.16em] text-paper-light/55">
                {roleLabels[user?.role || ""] || "Sistema"}
              </span>
            </span>
          </Link>
        </div>

        <nav aria-label="Navegación del panel" className="flex-1 space-y-1 overflow-y-auto p-3">
          <p className="px-3 pb-2 pt-3 font-mono text-[0.58rem] uppercase tracking-[0.18em] text-paper-light/40">Navegación</p>
          {links.map((link) => {
            const Icon = link.icon;
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={`group flex items-center gap-3 border border-transparent px-3 py-2.5 text-sm font-semibold transition ${
                  active
                    ? "border-yellow bg-yellow text-ink shadow-[3px_3px_0_#A92730]"
                    : "text-paper-light/70 hover:border-paper-light/20 hover:bg-paper-light/5 hover:text-paper-light"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-paper-light/15 p-3">
          <div className="flex items-center gap-3 border border-paper-light/15 bg-paper-light/5 p-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary font-mono text-xs font-bold text-white">{initials}</span>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-paper-light">{user?.nombre || "Usuario CUEP"}</p>
              <p className="truncate font-mono text-[0.58rem] uppercase tracking-[0.1em] text-paper-light/45">{user?.email || roleLabels[user?.role || ""] || "Sesión"}</p>
            </div>
          </div>
          <Image src="/identity/penguin.png" alt="" width={86} height={122} className="mx-auto mt-4 h-24 w-auto opacity-90" />
          <div className="mt-3 flex gap-2">
            <Link href="/" className="flex flex-1 items-center justify-center border border-paper-light/20 px-2 py-2 font-mono text-[0.58rem] font-semibold uppercase tracking-[0.08em] text-paper-light/70 transition hover:border-yellow hover:text-yellow">
              Sitio
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              className="flex flex-1 items-center justify-center gap-1.5 border border-paper-light/20 px-2 py-2 font-mono text-[0.58rem] font-semibold uppercase tracking-[0.08em] text-paper-light/70 transition hover:border-red-bright hover:text-red-bright"
            >
              <LogOut className="h-3 w-3" aria-hidden="true" />
              Salir
            </button>
          </div>
        </div>
      </aside>

      <div className="md:pl-[276px]">
        <header className="sticky top-0 z-30 border-b-[1.5px] border-ink bg-cream/95 backdrop-blur md:hidden">
          <div className="flex items-center justify-between gap-3 px-4 py-3">
            <Link href="/dashboard" className="flex items-center gap-2">
              <span className="grid h-9 w-9 -rotate-3 place-items-center border border-ink bg-primary shadow-[2px_2px_0_#171313]">
                <Image src="/identity/heart.png" alt="" width={22} height={22} className="h-5 w-5" />
              </span>
              <span className="font-display text-2xl uppercase leading-none text-primary">CUEP</span>
            </Link>
            <div className="flex items-center gap-2">
              <Image src="/identity/penguin.png" alt="" width={34} height={48} className="h-9 w-auto" />
              <button type="button" onClick={handleLogout} className="border border-ink px-2.5 py-1.5 font-mono text-[0.58rem] font-bold uppercase tracking-[0.08em] text-ink">
                Salir
              </button>
            </div>
          </div>
          <nav aria-label="Navegación móvil del panel" className="flex gap-1 overflow-x-auto px-3 pb-2">
            {links.map((link) => {
              const Icon = link.icon;
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex shrink-0 items-center gap-1.5 border px-2.5 py-1.5 font-mono text-[0.58rem] font-semibold uppercase tracking-[0.06em] ${
                    active ? "border-ink bg-yellow text-ink" : "border-ink/15 text-ink/65"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </header>

        <div className="hidden items-center justify-between border-b border-ink/10 px-6 py-3 md:flex lg:px-10">
          <div className="flex items-center gap-3">
            <span className="type-label text-ink/40">Panel</span>
            <span className="h-3 w-px bg-ink/20" aria-hidden="true" />
            <span className="font-mono text-[0.68rem] font-semibold uppercase tracking-[0.1em] text-ink/65">{displayTitle}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="type-stamp text-primary">{roleLabels[user?.role || ""] || "Sesión"}</span>
            <span className="font-mono text-[0.58rem] uppercase tracking-[0.1em] text-ink/40">CUEP · Sistema interno</span>
          </div>
        </div>

        <main className="px-4 py-6 sm:px-6 md:py-8 lg:px-10 lg:py-10">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
