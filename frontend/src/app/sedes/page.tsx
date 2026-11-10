"use client";

import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";

interface Sede {
  id: number;
  nombre: string;
  ciudad: string | null;
  descripcion: string | null;
  image_url: string | null;
  maps_url: string | null;
  activo: boolean;
}

export default function SedesPage() {
  const { data, isLoading } = useQuery<Sede[]>({
    queryKey: ["sedes-public"],
    queryFn: async () => (await api.get("/sedes")).data,
  });
  const sedes = (data || []).filter((sede) => sede.activo);

  return (
    <>
      <section className="border-b-[1.5px] border-ink bg-cream">
        <div className="container-site py-14 md:py-20">
          <p className="type-kicker">Dónde nos encontramos</p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
            <h1 className="font-display text-5xl uppercase leading-[0.9] text-primary md:text-7xl">
              Las sedes son el lugar donde el colectivo se encuentra
            </h1>
            <p className="type-deck max-w-lg">
              Espacios comunitarios donde estudiantes y tutores voluntarios se reúnen para preparar el examen de admisión, compartir materiales y sostener el acompañamiento.
            </p>
          </div>
        </div>
      </section>

      <section className="container-site py-12 md:py-16">
        {isLoading ? (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div key={item} className="h-80 animate-pulse border border-ink/15 bg-sand" />
            ))}
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {sedes.map((sede, index) => (
              <article key={sede.id} className="poster-card flex flex-col overflow-hidden">
                <div className="relative">
                  {sede.image_url ? (
                    <Image src={sede.image_url} alt={sede.nombre} width={520} height={300} className="h-48 w-full object-cover" />
                  ) : (
                    <div className="flex h-48 items-center justify-center bg-sand halftone text-primary" aria-hidden="true">
                      <Image src="/identity/heart.png" alt="" width={80} height={80} className="h-20 w-20 opacity-55" />
                    </div>
                  )}
                  <span className="absolute left-4 top-4 border border-ink bg-cream px-2 py-1 font-mono text-[0.62rem] font-bold uppercase tracking-[0.1em] text-ink">
                    Sede {String(index + 1).padStart(2, "0")}
                  </span>
                </div>
                <div className="flex flex-1 flex-col p-5 sm:p-6">
                  <p className="type-label text-ink/45">{sede.ciudad || "Puebla"}</p>
                  <h2 className="mt-2 font-display text-3xl uppercase leading-none text-primary">{sede.nombre}</h2>
                  {sede.descripcion ? (
                    <p className="mt-3 flex-1 font-editorial text-base leading-relaxed text-ink/70">{sede.descripcion}</p>
                  ) : (
                    <p className="mt-3 flex-1 font-editorial text-base leading-relaxed text-ink/45">Sede comunitaria del CUEP.</p>
                  )}
                  {sede.maps_url && (
                    <a href={sede.maps_url} target="_blank" rel="noreferrer" className="link-arrow mt-6 text-primary">
                      Ver ubicación
                    </a>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}

        {!isLoading && sedes.length === 0 && (
          <div className="poster-card flex flex-col items-center gap-5 p-8 text-center">
            <Image src="/identity/penguin.png" alt="" width={90} height={128} className="h-28 w-auto" />
            <div>
              <h2 className="font-display text-3xl uppercase text-primary">Estamos preparando las sedes</h2>
              <p className="mt-2 max-w-lg font-editorial text-base text-ink/60">Muy pronto publicaremos los espacios de esta convocatoria. Mientras tanto, puedes escribirnos o registrarte como tutor voluntario.</p>
            </div>
          </div>
        )}

        <div className="mt-10 flex flex-col gap-4 border-t border-ink/15 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-editorial text-lg text-ink/65">¿Quieres sumarte al colectivo?</p>
          <div className="flex flex-wrap gap-3">
            <Link href="/registro" className="btn-outline">Soy estudiante</Link>
            <Link href="/registro-tutor" className="btn-primary">Soy tutor voluntario</Link>
          </div>
        </div>
      </section>
    </>
  );
}
