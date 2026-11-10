import Image from "next/image";

type EmptyStateProps = {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  imageSrc?: string;
  imageAlt?: string;
};

export function EmptyState({
  title = "Sin registros",
  description = "Aún no hay información disponible.",
  actionLabel,
  onAction,
  imageSrc = "/identity/penguin.png",
  imageAlt = "Pingüino CUEP",
}: EmptyStateProps) {
  return (
    <div className="poster-card flex flex-col items-center justify-center px-5 py-12 text-center">
      <div className="grid h-24 w-24 place-items-center border border-ink/15 bg-sand halftone">
        <Image src={imageSrc} alt={imageAlt} width={74} height={104} className="h-20 w-auto" />
      </div>
      <p className="type-label mt-5 text-ink/40">Estado vacío</p>
      <h3 className="mt-2 font-display text-3xl uppercase text-primary">{title}</h3>
      <p className="mt-2 max-w-md font-editorial text-base leading-relaxed text-ink/65">{description}</p>
      {actionLabel && onAction && (
        <button className="btn-primary mt-6" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}
