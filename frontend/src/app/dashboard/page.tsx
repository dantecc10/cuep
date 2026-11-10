"use client";

import Image from "next/image";
import Link from "next/link";
import {
  BadgeCheck,
  BookOpen,
  CalendarClock,
  CalendarDays,
  ClipboardList,
  FileText,
  GraduationCap,
  Layers,
  MapPin,
  PlayCircle,
  Send,
  UserRound,
  Users,
  type LucideIcon,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { useAuthStore } from "@/store/auth";

type Acceso = { href: string; label: string; description: string; icon: LucideIcon };

const accesos: Record<string, Acceso[]> = {
  admin: [
    { href: "/dashboard/sedes", label: "Sedes", description: "Espacios y ubicaciones del colectivo.", icon: MapPin },
    { href: "/dashboard/planes", label: "Planes", description: "Organiza materias por plan de estudios.", icon: Layers },
    { href: "/dashboard/materias", label: "Materias", description: "Catálogo académico del CUEP.", icon: BookOpen },
    { href: "/dashboard/usuarios", label: "Usuarios", description: "Roles, accesos y coordinaciones.", icon: Users },
  ],
  coordinador: [
    { href: "/dashboard/grupos", label: "Grupos", description: "Abre grupos y revisa cupos.", icon: Users },
    { href: "/dashboard/tutores", label: "Tutores", description: "Carga docente y disponibilidad.", icon: GraduationCap },
    { href: "/dashboard/corridas", label: "Corridas", description: "Genera horarios para tu sede.", icon: PlayCircle },
    { href: "/dashboard/inscripciones", label: "Inscripciones", description: "Cupos, espera y pagos.", icon: ClipboardList },
    { href: "/dashboard/publicar", label: "Publicar", description: "Publica horarios aprobados.", icon: Send },
  ],
  subcoordinador: [
    { href: "/dashboard/grupos", label: "Grupos", description: "Abre grupos y revisa cupos.", icon: Users },
    { href: "/dashboard/tutores", label: "Tutores", description: "Carga docente y disponibilidad.", icon: GraduationCap },
    { href: "/dashboard/corridas", label: "Corridas", description: "Genera horarios para tu sede.", icon: PlayCircle },
    { href: "/dashboard/inscripciones", label: "Inscripciones", description: "Cupos, espera y pagos.", icon: ClipboardList },
    { href: "/dashboard/publicar", label: "Publicar", description: "Publica horarios aprobados.", icon: Send },
  ],
  tutor: [
    { href: "/dashboard/disponibilidad", label: "Disponibilidad", description: "Marca los horarios en que puedes dar asesoría.", icon: CalendarClock },
    { href: "/dashboard/materias", label: "Materias", description: "Consulta el catálogo académico.", icon: BookOpen },
    { href: "/dashboard/mi-horario", label: "Mi horario", description: "Revisa tus asesorías asignadas.", icon: CalendarDays },
  ],
  alumno: [
    { href: "/mi-inscripcion", label: "Mi inscripción", description: "Elige grupos y revisa tu lugar.", icon: FileText },
    { href: "/mi-perfil", label: "Mi perfil", description: "Completa tus datos de aspirante.", icon: UserRound },
    { href: "/mi-credencial", label: "Mi credencial", description: "Consulta y descarga tu credencial.", icon: BadgeCheck },
    { href: "/mi-horario", label: "Mi horario", description: "Consulta tus asesorías publicadas.", icon: CalendarDays },
  ],
};

const roleLabels: Record<string, string> = {
  admin: "Administración",
  coordinador: "Coordinación",
  subcoordinador: "Subcoordinación",
  tutor: "Tutoría",
  alumno: "Estudiante",
};

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const role = user?.role || "alumno";
  const items = accesos[role] || accesos.alumno;
  const today = new Intl.DateTimeFormat("es-MX", { weekday: "long", day: "numeric", month: "long" }).format(new Date());

  return (
    <AppShell title="Panel">
      <div className="space-y-8">
        <section className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <div className="poster-card p-6 sm:p-8">
            <p className="type-kicker">{roleLabels[role] || "Sesión"}</p>
            <h1 className="mt-3 max-w-2xl font-display text-4xl uppercase leading-[0.94] text-primary md:text-5xl">
              Hola, {user?.nombre || "bienvenida"}. Sigamos construyendo colectivo.
            </h1>
            <p className="type-deck mt-4 max-w-xl text-base">
              Este es tu panel de trabajo del CUEP. Desde aquí puedes coordinar sedes, grupos, tutorías, inscripciones y horarios.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <span className="type-stamp text-primary">{today}</span>
              <span className="type-stamp text-ink/60">{roleLabels[role] || "Sesión activa"}</span>
            </div>
          </div>

          <div className="poster-card poster-card--paper flex flex-col justify-between overflow-hidden p-5">
            <div>
              <p className="type-label text-ink/55">Manifiesto CUEP</p>
              <p className="mt-3 font-editorial text-2xl font-semibold leading-tight text-ink">
                Coordinar también es acompañar.
              </p>
            </div>
            <div className="mt-4 flex items-end justify-between gap-3">
              <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={105} height={149} className="h-28 w-auto" />
              <Image src="/identity/heart.png" alt="" width={44} height={44} className="h-10 w-10 opacity-80" />
            </div>
          </div>
        </section>

        <section>
          <div className="flex flex-col gap-2 border-b border-ink/15 pb-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="type-label text-ink/40">Accesos rápidos</p>
              <h2 className="mt-1 font-display text-3xl uppercase text-ink">Tu trabajo en el colectivo</h2>
            </div>
            <p className="font-mono text-[0.62rem] uppercase tracking-[0.1em] text-ink/45">{items.length} módulos disponibles</p>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item, index) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="poster-card group flex flex-col justify-between p-5 transition hover:-translate-y-1 hover:shadow-[7px_7px_0_#A92730]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="grid h-10 w-10 place-items-center border border-ink bg-sand text-primary">
                      <Icon className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span className="font-mono text-xs font-bold text-ink/30">{String(index + 1).padStart(2, "0")}</span>
                  </div>
                  <div className="mt-6">
                    <h3 className="font-display text-2xl uppercase text-ink group-hover:text-primary">{item.label}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-ink/60">{item.description}</p>
                  </div>
                  <span className="link-arrow mt-5 text-primary">Abrir módulo</span>
                </Link>
              );
            })}
          </div>
        </section>

        <section className="border-[1.5px] border-ink bg-ink p-6 text-paper-light sm:p-8">
          <div className="grid gap-6 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <p className="type-kicker type-kicker--light">Recordatorio</p>
              <h2 className="mt-3 font-display text-3xl uppercase text-yellow">La organización sostiene el acceso</h2>
              <p className="mt-3 max-w-2xl font-editorial text-base leading-relaxed text-paper-light/70">
                Cada grupo, sede y horario que coordinas abre una posibilidad real para alguien que quiere estudiar. Revisa tus módulos y mantén la información al día.
              </p>
            </div>
            <Link href="/" className="btn-outline border-yellow text-yellow hover:bg-yellow hover:text-ink">Ver sitio público</Link>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
