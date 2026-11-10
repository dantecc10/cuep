import { HeroSection } from "@/components/layout/hero-section";
import { PaperSection } from "@/components/layout/paper-section";
import { SectionHeading } from "@/components/layout/section-heading";
import { CallToAction } from "@/components/layout/call-to-action";

export default function Home() {
  return (
    <>
      <HeroSection />
      <PaperSection className="py-12">
        <div className="container-site space-y-6">
          <SectionHeading
            eyebrow="Educación popular"
            title="Organización colectiva y acceso al conocimiento"
            description="El CUEP coordina asesorías para aspirantes a la BUAP, cuidando la identidad gráfica del colectivo y la usabilidad de la plataforma."
          />
          <div className="grid gap-4 md:grid-cols-3">
            <article className="bg-surface border border-primary rounded-card p-5 poster-shadow">
              <h3 className="font-display text-2xl uppercase text-primary">Tutores</h3>
              <p className="mt-2 text-sm">Disponibilidad, materias y carga académica.</p>
            </article>
            <article className="bg-surface border border-primary rounded-card p-5">
              <h3 className="font-display text-2xl uppercase text-primary">Grupos</h3>
              <p className="mt-2 text-sm">Oferta por sede, nivel y área.</p>
            </article>
            <article className="bg-surface border border-primary rounded-card p-5">
              <h3 className="font-display text-2xl uppercase text-primary">Horarios</h3>
              <p className="mt-2 text-sm">Generación optimizada con restricciones reales.</p>
            </article>
          </div>
        </div>
      </PaperSection>
      <CallToAction />
    </>
  );
}
