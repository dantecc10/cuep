import Image from "next/image";

type EmptyStateProps = {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  imageSrc?: string;
  imageAlt?: string;
};

export function EmptyState({ title = "Sin registros", description = "Aún no hay información disponible.", actionLabel, onAction, imageSrc = "/identity/penguin.png", imageAlt = "Pingüino CUEP" }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <Image src={imageSrc} alt={imageAlt} width={96} height={136} className="mb-4 opacity-80" />
      <h3 className="font-display text-2xl uppercase text-primary mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-md mb-6">{description}</p>
      {actionLabel && onAction && <button className="btn-primary" onClick={onAction}>{actionLabel}</button>}
    </div>
  );
}
