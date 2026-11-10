import { ReactNode } from "react";

export function PaperSection({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`paper-surface ${className}`}>{children}</section>;
}
