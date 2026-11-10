import Link from "next/link";
import Image from "next/image";

export function HeroSection() {
  return (
    <section className="bg-background">
      <div className="container-site grid gap-8 py-12 md:py-20 md:grid-cols-[1.15fr_0.85fr] items-center">
        <div className="space-y-6">
          <p className="font-semibold text-secondary uppercase tracking-wide text-sm">Educación popular y acceso al conocimiento</p>
          <h1 className="font-display text-5xl md:text-7xl uppercase text-primary leading-none">
            Horarios que organizan la comunidad
          </h1>
          <p className="font-editorial text-xl md:text-2xl max-w-xl">
            El CUEP coordina asesorías para aspirantes a la BUAP con una identidad de cartelería popular: clara, colectiva y accesible.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/registro" className="btn-primary">Registrarme</Link>
            <Link href="/login" className="inline-flex items-center justify-center px-5 py-3 border border-primary text-primary font-bold rounded-button hover:bg-primary hover:text-white transition">
              Iniciar sesión
            </Link>
          </div>
        </div>
        <div className="relative">
          <div className="absolute -right-4 -bottom-4 h-full w-full bg-paper rounded-card" aria-hidden="true" />
          <div className="relative bg-surface border border-primary rounded-card poster-shadow p-6 md:p-8 space-y-4">
            <Image src="/identity/heart.svg" alt="Corazón ornamental del colectivo" width={96} height={96} />
            <p className="font-display text-3xl uppercase text-primary">Participa y aprende</p>
            <p className="text-sm">Convocatorias, cursos y asesorías organizadas por sede.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
