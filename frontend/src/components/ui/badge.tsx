import { ReactNode } from "react";

const variants: Record<string, string> = {
  default: "bg-primary text-white",
  secondary: "bg-paper text-text",
  destructive: "bg-red-100 text-red-700",
};

export function Badge({ children, variant = "default", className = "" }: { children: ReactNode; variant?: string; className?: string }) {
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${variants[variant] || variants.default} ${className}`}>{children}</span>;
}
