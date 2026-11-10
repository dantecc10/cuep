import Link from "next/link";
import { DualMark } from "@/components/layout/dual-mark";

export function SiteFooter() {
  return (
    <footer className="mt-20 border-t-[1.5px] border-ink bg-ink text-paper-light">
      <div className="container-site grid gap-10 py-12 md:grid-cols-[1.3fr_0.7fr_0.7fr]">
        <div>
          <div className="flex items-center gap-3">
            <DualMark variant="dark" size="md" />
            <p className="font-display text-3xl uppercase text-yellow">CUEP</p>
          </div>
          <p className="mt-4 max-w-md font-editorial text-lg leading-relaxed text-paper-light/80">
            Colectivo Universitario por la Educación Popular. Construimos espacios de aprendizaje, acompañamiento y organización para aspirantes a la BUAP.
          </p>
          <p className="mt-6 inline-flex border border-accent/70 px-3 py-1.5 font-mono text-[0.62rem] font-semibold uppercase tracking-[0.16em] text-accent">
            Puebla, México
          </p>
        </div>

        <div>
          <p className="type-label text-accent">El colectivo</p>
          <nav className="mt-4 space-y-2.5 text-sm text-paper-light/80" aria-label="Enlaces del colectivo">
            <p><Link href="/#colectivo" className="hover:text-accent">Quiénes somos</Link></p>
            <p><Link href="/sedes" className="hover:text-accent">Sedes</Link></p>
            <p><Link href="/#convocatorias" className="hover:text-accent">Convocatorias</Link></p>
            <p><Link href="/#participa" className="hover:text-accent">Participa</Link></p>
          </nav>
        </div>

        <div>
          <p className="type-label text-accent">Contacto</p>
          <div className="mt-4 space-y-2.5 text-sm text-paper-light/80">
            <p>educacionpopular@cuep.org</p>
            <p>Redes sociales del colectivo</p>
            <p className="pt-4 font-mono text-[0.62rem] uppercase tracking-[0.12em] text-paper-light/50">
              Hecho en colectivo · {new Date().getFullYear()}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
