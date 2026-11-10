import Link from "next/link";
import Image from "next/image";

export function SiteHeader() {
  return (
    <header className="bg-background border-b border-primary/20">
      <div className="container-site flex items-center justify-between py-4">
        <Link href="/" className="flex items-center gap-3 font-display text-2xl uppercase tracking-wide text-primary">
          <Image src="/identity/heart.png" alt="Logotipo CUEP" width={36} height={36} />
          <span>CUEP</span>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm font-semibold">
          <Link href="/login" className="hover:text-primary">Iniciar sesión</Link>
          <Link href="/registro" className="hover:text-primary">Registrarse</Link>
        </nav>
        <Link href="/registro" className="btn-primary text-sm">
          Participar
        </Link>
      </div>
    </header>
  );
}
