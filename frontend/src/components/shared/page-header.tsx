import { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  actions,
  eyebrow,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="border-b border-ink/15 pb-6">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div className="max-w-2xl">
          <p className="type-kicker">{eyebrow || "Sistema interno"}</p>
          <h1 className="mt-3 font-display text-4xl uppercase leading-[0.92] text-primary md:text-5xl">{title}</h1>
          {description && <p className="type-deck mt-3 text-base">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </div>
  );
}
