import Link from "next/link";
import Image from "next/image";
import { DualMark } from "@/components/layout/dual-mark";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden border-b-[1.5px] border-ink bg-cream">
      <div className="pointer-events-none absolute -right-24 top-10 hidden h-72 w-72 rounded-full bg-yellow/30 blur-3xl md:block" aria-hidden="true" />
      <div className="container-site relative grid items-center gap-10 py-14 md:grid-cols-[1.12fr_0.88fr] md:py-20 lg:py-24">
        <div className="animate-rise">
          <p className="type-kicker">Colectivo Universitario por la Educación Popular</p>
          <h1 className="mt-5 max-w-3xl font-display text-[3.35rem] uppercase leading-[0.9] text-primary sm:text-7xl lg:text-[5.5rem]">
            La educación
            <span className="block text-ink">se construye</span>
            <span className="block">
              <span className="marker">en colectivo</span>
            </span>
          </h1>
          <p className="type-deck mt-6 max-w-xl">
            Somos estudiantes y tutores voluntarios que acompañan a aspirantes a la BUAP con asesorías gratuitas, organización comunitaria y espacios donde nadie aprende en soledad.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link href="#colectivo" className="btn-primary">Conoce el colectivo</Link>
            <Link href="/registro" className="btn-outline">Quiero participar</Link>
          </div>
          <div className="mt-9 flex flex-wrap gap-x-8 gap-y-3 border-t border-ink/15 pt-5">
            <p className="type-label text-ink/60"><span className="text-primary">01</span> Asesorías gratuitas</p>
            <p className="type-label text-ink/60"><span className="text-primary">02</span> Tutores voluntarios</p>
            <p className="type-label text-ink/60"><span className="text-primary">03</span> Sedes comunitarias</p>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-md animate-rise-delayed lg:max-w-lg">
          <div className="absolute -left-4 top-8 hidden h-24 w-24 rotate-6 border-[1.5px] border-ink bg-accent/80 md:block" aria-hidden="true" />
          <div className="absolute -right-4 bottom-8 hidden h-20 w-20 -rotate-6 border-[1.5px] border-ink bg-yellow md:block" aria-hidden="true" />
          <div className="relative border-[1.5px] border-ink bg-surface p-5 shadow-[8px_8px_0_#A92730] sm:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="type-label text-primary">Manifiesto</p>
                <p className="mt-2 font-editorial text-2xl font-semibold leading-tight text-ink">
                  Nadie se forma solo. Aprender también es organizarse.
                </p>
              </div>
              <DualMark size="md" />
            </div>
            <div className="mt-6 flex items-end justify-between gap-4 border-t border-ink/15 pt-5">
              <Image
                src="/identity/penguin.png"
                alt="Pingüino del CUEP"
                width={150}
                height={212}
                className="h-36 w-auto object-contain sm:h-44"
                priority
              />
              <div className="pb-2 text-right">
                <p className="type-stamp animate-stamp text-primary">Desde Puebla</p>
                <p className="mt-4 font-mono text-[0.62rem] uppercase tracking-[0.16em] text-ink/50">
                  Educación popular<br />Acceso a la universidad
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
