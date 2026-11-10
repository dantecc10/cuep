import { ReactNode } from "react";

const variants: Record<string, string> = {
  default: "border border-ink bg-primary text-white",
  secondary: "border border-ink/30 bg-sand text-ink",
  accent: "border border-ink bg-accent text-ink",
  destructive: "border border-red-800 bg-red-100 text-red-800",
};

export function Badge({ children, variant = "default", className = "" }: { children: ReactNode; variant?: string; className?: string }) {
  return <span className={`inline-flex items-center border px-2 py-0.5 font-mono text-[0.6rem] font-bold uppercase tracking-[0.08em] ${variants[variant] || variants.default} ${className}`}>{children}</span>;
}
