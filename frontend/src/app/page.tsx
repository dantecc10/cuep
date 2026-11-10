"use client";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";
import { HeroSection } from "@/components/layout/hero-section";
import { PaperSection } from "@/components/layout/paper-section";
import { SectionHeading } from "@/components/layout/section-heading";
import { CallToAction } from "@/components/layout/call-to-action";

interface Sede { id: number; nombre: string; ciudad: string | null; descripcion: string | null; image_url: string | null; maps_url: string | null; activo?: boolean; }
interface Corrida { id: number; sede_id: number | null; estado: string; publicada: boolean; }

export default function Home() {
  const { data: sedes } = useQuery<Sede[]>({ queryKey: ["sedes-public"], queryFn: async () => (await api.get("/sedes")).data });
  const { data: corridas } = useQuery<Corrida[]>({ queryKey: ["convocatorias"], queryFn: async () => (await api.get("/corridas", { params: { publicada: true } })).data });

  return (
    <>
      <HeroSection />
      <section className="container-site py-12 space-y-6">
        <SectionHeading eyebrow="Quiénes somos" title="Educación popular y organización colectiva" description="El CUEP coordina asesorías para aspirantes a la BUAP. Trabajamos con tutores voluntarios, sedes comunitarias y una identidad de cartelería popular." />
        <div className="grid gap-4 md:grid-cols-3">
          <article className="bg-surface border border-primary rounded-card p-5 poster-shadow">
            <h3 className="font-display text-2xl uppercase text-primary">Comunidad</h3>
            <p className="mt-2 text-sm">Acompañamiento entre estudiantes y tutores voluntarios.</p>
          </article>
          <article className="bg-surface border border-primary rounded-card p-5">
            <h3 className="font-display text-2xl uppercase text-primary">Acceso</h3>
            <p className="mt-2 text-sm">Cursos gratuitos para el examen de admisión.</p>
          </article>
          <article className="bg-surface border border-primary rounded-card p-5">
            <h3 className="font-display text-2xl uppercase text-primary">Organización</h3>
            <p className="mt-2 text-sm">Horarios y sedes coordinados de forma colectiva.</p>
          </article>
        </div>
      </section>
      <PaperSection className="py-12 torn-edge">
        <div className="container-site space-y-6">
          <SectionHeading eyebrow="Sedes" title="Dónde participar" description="Consulta las sedes activas y su ubicación." />
          <div className="grid gap-4 md:grid-cols-3">
            {(sedes || []).filter((s) => s.activo !== false).map((sede) => (
              <article key={sede.id} className="bg-surface border border-primary rounded-card p-5">
                {sede.image_url && <Image src={sede.image_url} alt={sede.nombre} width={320} height={180} className="w-full h-32 object-cover rounded-card mb-3" />}
                <h3 className="font-display text-2xl uppercase text-primary">{sede.nombre}</h3>
                {sede.ciudad && <p className="text-sm">{sede.ciudad}</p>}
                {sede.descripcion && <p className="text-sm mt-2">{sede.descripcion}</p>}
                {sede.maps_url && <a href={sede.maps_url} className="btn-primary mt-3 inline-flex" target="_blank" rel="noreferrer">Ver en Google Maps</a>}
              </article>
            ))}
          </div>
        </div>
      </PaperSection>
      <section className="container-site py-12 space-y-6">
        <SectionHeading eyebrow="Convocatorias" title="Próximas actividades" description="Horarios publicados y actividades del colectivo." />
        <div className="grid gap-4 md:grid-cols-2">
          {(corridas || []).filter((c) => c.publicada).map((c) => (
            <article key={c.id} className="bg-surface border border-primary rounded-card p-5 poster-shadow">
              <h3 className="font-display text-2xl uppercase text-primary">Corrida #{c.id}</h3>
              <p className="text-sm mt-2">Sede {c.sede_id} — {c.estado}</p>
            </article>
          ))}
          {!corridas?.some((c) => c.publicada) && <p className="text-sm text-muted-foreground">Aún no hay convocatorias publicadas.</p>}
        </div>
      </section>
      <section className="container-site py-12 space-y-6">
        <SectionHeading eyebrow="Participa" title="Únete al colectivo" description="Elige cómo quieres participar." />
        <div className="grid gap-4 md:grid-cols-2">
          <Link href="/registro" className="bg-surface border border-primary rounded-card p-6 hover:bg-paper transition">
            <h3 className="font-display text-2xl uppercase text-primary">Soy estudiante</h3>
            <p className="mt-2 text-sm">Regístrate para recibir asesorías y consultar tu horario.</p>
          </Link>
          <Link href="/registro-tutor" className="bg-surface border border-primary rounded-card p-6 hover:bg-paper transition">
            <h3 className="font-display text-2xl uppercase text-primary">Soy tutor voluntario</h3>
            <p className="mt-2 text-sm">Ofrece tu tiempo y conocimientos para acompañar aspirantes.</p>
          </Link>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/login" className="btn-primary">Acceso al sistema</Link>
        </div>
      </section>
      <CallToAction />
    </>
  );
}
