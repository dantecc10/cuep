"use client";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { ReactNode } from "react";

export function ThemeProvider({ children, defaultTheme = "light", enableSystem = false }: { children: ReactNode; defaultTheme?: string; enableSystem?: boolean }) {
  return <NextThemesProvider attribute="class" defaultTheme={defaultTheme} enableSystem={enableSystem}>{children}</NextThemesProvider>;
}
