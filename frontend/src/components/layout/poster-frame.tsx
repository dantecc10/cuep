import Image from "next/image";

type PosterFrameProps = {
  title: string;
  subtitle?: string;
  imageSrc?: string;
  imageAlt?: string;
};

export function PosterFrame({ title, subtitle, imageSrc = "/identity/heart.svg", imageAlt = "Emblema del colectivo" }: PosterFrameProps) {
  return (
    <div className="relative">
      <div className="absolute -right-3 -bottom-3 h-full w-full bg-paper rounded-card" aria-hidden="true" />
      <div className="relative bg-surface border border-primary rounded-card poster-shadow p-6 md:p-8">
        <div className="grid gap-6 md:grid-cols-[1fr_120px] items-center">
          <div>
            <p className="font-editorial text-lg text-secondary">{subtitle}</p>
            <h2 className="font-display text-4xl md:text-5xl uppercase text-primary leading-none mt-2">{title}</h2>
          </div>
          <Image src={imageSrc} alt={imageAlt} width={120} height={120} className="justify-self-center" />
        </div>
      </div>
    </div>
  );
}
