import Link from "next/link";
import Image from "next/image";

export function CallToAction() {
  return (
    <section className="container-site py-16 md:py-24">
      <div className="relative overflow-hidden border-[1.5px] border-ink bg-primary p-7 text-white shadow-[8px_8px_0_#171313] sm:p-10 md:p-14">
        <div className="absolute -right-14 -top-14 h-48 w-48 rounded-full border-[1.5px] border-yellow/40" aria-hidden="true" />
        <div className="absolute -bottom-20 right-24 hidden h-56 w-56 rounded-full bg-yellow/20 blur-2xl md:block" aria-hidden="true" />
        <div className="relative grid gap-8 md:grid-cols-[1fr_auto] md:items-end">
          <div>
            <p className="type-kicker type-kicker--light">Súmate al colectivo</p>
            <h2 className="mt-4 max-w-3xl font-display text-4xl uppercase leading-[0.92] text-white md:text-6xl">
              La universidad también se abre en comunidad
            </h2>
            <p className="mt-5 max-w-xl font-editorial text-lg leading-relaxed text-white/80">
              Si estás preparando tu examen o quieres acompañar a quien lo está haciendo, hay un lugar para ti en el CUEP.
            </p>
          </div>
          <div className="flex flex-col items-start gap-4 md:items-end">
            <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={110} height={156} className="h-28 w-auto md:h-36" />
            <Link href="/registro" className="btn-primary border-white bg-white text-primary shadow-[3px_3px_0_#171313] hover:bg-yellow hover:text-ink">
              Quiero participar
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
