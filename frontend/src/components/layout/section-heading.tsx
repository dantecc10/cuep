type Props = { eyebrow?: string; title: string; description?: string };

export function SectionHeading({ eyebrow, title, description }: Props) {
  return (
    <div className="space-y-2">
      {eyebrow && <p className="font-semibold text-secondary uppercase tracking-wide text-sm">{eyebrow}</p>}
      <h2 className="font-display text-3xl md:text-4xl uppercase text-primary">{title}</h2>
      {description && <p className="font-editorial text-lg max-w-2xl">{description}</p>}
    </div>
  );
}
