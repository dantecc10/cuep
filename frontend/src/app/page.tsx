"use client";

import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";
import { HeroSection } from "@/components/layout/hero-section";
import { PaperSection } from "@/components/layout/paper-section";
import { SectionHeading } from "@/components/layout/section-heading";
import { CallToAction } from "@/components/layout/call-to-action";

interface Sede {
  id: number;
  nombre: string;
  ciudad: string | null;
  descripcion: string | null;
  image_url: string | null;
  maps_url: string | null;
  activo?: boolean;
}

interface Corrida {
  id: number;
  sede_id: number | null;
  estado: string;
  publicada: boolean;
}

const principios = [
  {
    numero: "01",
    titulo: "Acompañamiento",
    texto: "Nadie enfrenta el examen de admisión en soledad. Estudiantes y tutores comparten tiempo, apuntes y experiencia.",
  },
  {
    numero: "02",
    titulo: "Gratuidad",
    texto: "El acceso al conocimiento no se cobra. Las asesorías son un espacio abierto para quien quiera aprender.",
  },
  {
    numero: "03",
    titulo: "Organización",
    texto: "Coordinar sedes, horarios y grupos también es una forma de hacer comunidad y sostener el proyecto entre todas.",
  },
];

export default function Home() {
  const { data: sedes } = useQuery<Sede[]>({
    queryKey: ["sedes-public"],
    queryFn: async () => (await api.get("/sedes")).data,
  });
  const { data: corridas } = useQuery<Corrida[]>({
    queryKey: ["convocatorias"],
    queryFn: async () => (await api.get("/corridas", { params: { publicada: true } })).data,
  });

  const sedesActivas = (sedes || []).filter((sede) => sede.activo !== false);
  const sedeNombre = (id: number | null) => sedesActivas.find((sede) => sede.id === id)?.nombre;
  const convocatorias = (corridas || []).filter((corrida) => corrida.publicada);

  return (
    <>
      <HeroSection />

      <section id="colectivo" className="container-site scroll-mt-24 py-16 md:py-24">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
          <div>
            <SectionHeading eyebrow="01 · El colectivo" title="Una red de estudiantes que no deja a nadie atrás" />
            <p className="type-label mt-6 text-ink/50">Colectivo Universitario por la Educación Popular · BUAP</p>
          </div>
          <div className="space-y-7">
            <p className="type-quote">
              Creemos que la educación es un derecho, no un privilegio. Por eso la organizamos en colectivo.
            </p>
            <div className="space-y-4 font-editorial text-base leading-relaxed text-ink/80">
              <p>
                El CUEP nace del encuentro entre estudiantes que ya recorrieron el camino y aspirantes que quieren llegar a la universidad. No somos una academia ni una empresa: somos una red de acompañamiento voluntario.
              </p>
              <p>
                Trabajamos con asesorías gratuitas, sedes comunitarias y una organización horizontal donde tutores, estudiantes y coordinaciones sostienen el proyecto entre todas las personas.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {principios.map((principio) => (
                <article key={principio.numero} className="poster-card p-4">
                  <p className="font-mono text-xs font-bold text-primary">{principio.numero}</p>
                  <h3 className="mt-3 font-display text-2xl uppercase text-ink">{principio.titulo}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-ink/70">{principio.texto}</p>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="border-y-[1.5px] border-ink bg-ink py-14 text-paper-light md:py-20">
        <div className="container-site grid gap-8 md:grid-cols-[1fr_auto] md:items-end">
          <div>
            <p className="type-kicker type-kicker--light">Lo que hacemos</p>
            <h2 className="mt-4 max-w-4xl font-display text-4xl uppercase leading-[0.94] text-yellow md:text-6xl">
              Asesorías, comunidad y organización para llegar a la universidad
            </h2>
          </div>
          <p className="max-w-md font-editorial text-lg leading-relaxed text-paper-light/75">
            Preparamos el examen de admisión, acompañamos el proceso y construimos espacios donde aprender también sea un acto colectivo.
          </p>
        </div>
      </section>

      <PaperSection className="torn-edge py-16 md:py-24">
        <div className="container-site space-y-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <SectionHeading eyebrow="02 · Sedes" title="Dónde nos encontramos" description="Espacios comunitarios donde el colectivo se reúne para acompañar y aprender." />
            <Link href="/sedes" className="link-arrow shrink-0 text-ink">Ver todas las sedes</Link>
          </div>

          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {sedesActivas.map((sede) => (
              <article key={sede.id} className="poster-card flex flex-col overflow-hidden">
                {sede.image_url ? (
                  <Image src={sede.image_url} alt={sede.nombre} width={480} height={280} className="h-44 w-full object-cover" />
                ) : (
                  <div className="flex h-44 items-center justify-center bg-sand halftone text-primary" aria-hidden="true">
                    <Image src="/identity/heart.png" alt="" width={72} height={72} className="h-16 w-16 opacity-60" />
                  </div>
                )}
                <div className="flex flex-1 flex-col p-5">
                  <p className="type-label text-ink/50">{sede.ciudad || "Puebla"}</p>
                  <h3 className="mt-2 font-display text-3xl uppercase text-primary">{sede.nombre}</h3>
                  {sede.descripcion && <p className="mt-3 flex-1 text-sm leading-relaxed text-ink/70">{sede.descripcion}</p>}
                  {sede.maps_url && (
                    <a href={sede.maps_url} className="link-arrow mt-5 text-primary" target="_blank" rel="noreferrer">
                      Ver ubicación
                    </a>
                  )}
                </div>
              </article>
            ))}
            {sedesActivas.length === 0 && (
              <p className="col-span-full border border-dashed border-ink/30 p-6 font-editorial text-lg text-ink/60">
                Estamos preparando las sedes de esta convocatoria. Vuelve pronto o escríbenos para sumarte.
              </p>
            )}
          </div>
        </div>
      </PaperSection>

      <section id="convocatorias" className="container-site scroll-mt-24 py-16 md:py-24">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <SectionHeading
            eyebrow="03 · Convocatorias"
            title="Actividades abiertas del colectivo"
            description="Horarios publicados, sesiones de asesoría y actividades comunitarias."
          />
          <div className="space-y-3">
            {convocatorias.map((corrida) => (
              <article key={corrida.id} className="poster-card flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="type-label text-primary">Convocatoria #{corrida.id}</p>
                  <h3 className="mt-1 font-display text-2xl uppercase text-ink">
                    Asesorías en {sedeNombre(corrida.sede_id) || "sede por confirmar"}
                  </h3>
                </div>
                <span className="type-stamp shrink-0 text-ink/70">{corrida.estado}</span>
              </article>
            ))}
            {convocatorias.length === 0 && (
              <div className="poster-card flex items-center gap-4 p-5">
                <Image src="/identity/penguin.png" alt="" width={64} height={90} className="h-20 w-auto" />
                <div>
                  <h3 className="font-display text-2xl uppercase text-primary">Próxima convocatoria</h3>
                  <p className="mt-1 text-sm text-ink/70">Aún no hay horarios publicados. Síguenos o regístrate para recibir información.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <section id="participa" className="container-site scroll-mt-24 py-16 md:py-24">
        <SectionHeading
          eyebrow="04 · Participa"
          title="Hay muchas formas de sumarte"
          description="Puedes llegar como estudiante, ofrecer tu tiempo como tutor voluntario o acompañar desde tu comunidad."
        />
        <div className="mt-8 grid gap-5 md:grid-cols-2">
          <Link href="/registro" className="poster-card group flex flex-col justify-between p-6 transition hover:-translate-y-1 hover:shadow-[7px_7px_0_#A92730] sm:p-8">
            <div>
              <p className="type-label text-primary">Para aspirantes</p>
              <h3 className="mt-3 font-display text-4xl uppercase text-ink">Soy estudiante</h3>
              <p className="mt-3 max-w-md font-editorial text-base leading-relaxed text-ink/70">
                Regístrate para recibir asesorías gratuitas, consultar tu horario y formar parte de una comunidad que te acompaña.
              </p>
            </div>
            <span className="link-arrow mt-8 text-primary">Quiero asesorías</span>
          </Link>

          <Link href="/registro-tutor" className="poster-card poster-card--ink group flex flex-col justify-between p-6 transition hover:-translate-y-1 hover:shadow-[7px_7px_0_#E8B83E] sm:p-8">
            <div>
              <p className="type-label text-yellow">Para tutores</p>
              <h3 className="mt-3 font-display text-4xl uppercase text-paper-light">Soy tutor voluntario</h3>
              <p className="mt-3 max-w-md font-editorial text-base leading-relaxed text-paper-light/75">
                Comparte tu tiempo y tus conocimientos. Acompaña a quienes están construyendo su camino a la universidad.
              </p>
            </div>
            <span className="link-arrow mt-8 text-yellow">Quiero acompañar</span>
          </Link>
        </div>

        <div className="mt-8 flex flex-col gap-4 border-t border-ink/20 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-editorial text-lg text-ink/70">¿Ya formabas parte del colectivo?</p>
          <Link href="/login" className="btn-outline">Acceso al sistema</Link>
        </div>
      </section>

      <CallToAction />
    </>
  );
}
