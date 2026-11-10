import Link from "next/link";
import Image from "next/image";

const links = [
  { href: "/#colectivo", label: "El colectivo" },
  { href: "/sedes", label: "Sedes" },
  { href: "/#convocatorias", label: "Convocatorias" },
  { href: "/#participa", label: "Participa" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b-[1.5px] border-ink bg-cream/95 backdrop-blur">
      <div className="container-site flex items-center justify-between gap-4 py-3">
        <Link href="/" className="group flex items-center gap-3 text-ink">
          <span className="grid h-11 w-11 -rotate-3 place-items-center border-[1.5px] border-ink bg-primary shadow-[3px_3px_0_#171313] transition-transform group-hover:rotate-0">
            <Image src="/identity/heart.png" alt="" width={28} height={28} className="h-7 w-7" />
          </span>
          <span className="leading-none">
            <span className="block font-display text-2xl uppercase tracking-wide text-primary">CUEP</span>
            <span className="mt-1 hidden font-mono text-[0.55rem] font-semibold uppercase tracking-[0.16em] text-ink/70 sm:block">
              Educación popular · BUAP
            </span>
          </span>
        </Link>

        <nav aria-label="Navegación principal" className="hidden items-center gap-1 lg:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="border border-transparent px-3 py-2 font-mono text-[0.68rem] font-semibold uppercase tracking-[0.1em] text-ink/75 transition hover:border-ink hover:bg-yellow hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link href="/login" className="btn-outline hidden sm:inline-flex">Entrar</Link>
          <Link href="/registro" className="btn-primary">Súmate</Link>
        </div>
      </div>
      <nav aria-label="Navegación móvil" className="flex gap-1 overflow-x-auto border-t border-ink/10 px-4 py-2 lg:hidden">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="shrink-0 px-2 py-1 font-mono text-[0.62rem] font-semibold uppercase tracking-[0.08em] text-ink/70"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
