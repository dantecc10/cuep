type Props = { eyebrow?: string; title: string; description?: string };

export function SectionHeading({ eyebrow, title, description }: Props) {
  return (
    <div className="max-w-3xl">
      {eyebrow && <p className="type-kicker">{eyebrow}</p>}
      <h2 className="mt-4 font-display text-4xl uppercase leading-[0.94] text-primary md:text-5xl">{title}</h2>
      {description && <p className="type-deck mt-4 max-w-2xl">{description}</p>}
    </div>
  );
}
