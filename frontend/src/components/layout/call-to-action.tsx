import Link from "next/link";

export function CallToAction() {
  return (
    <section className="container-site py-12">
      <div className="bg-primary text-white rounded-card p-8 md:p-12 grid gap-6 md:grid-cols-[1fr_auto] items-center poster-shadow">
        <div>
          <h2 className="font-display text-4xl uppercase leading-none text-white">Inscríbete y construye tu horario</h2>
          <p className="mt-3 max-w-2xl text-white">Regístrate, elige tu sede y nivel, e inscríbete a grupos disponibles.</p>
        </div>
        <Link href="/registro" className="btn-primary bg-white text-primary hover:bg-paper-light">Registrarme</Link>
      </div>
    </section>
  );
}
