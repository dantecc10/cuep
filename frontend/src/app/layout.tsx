import type { Metadata } from "next";
import { Anton, Roboto_Slab, Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { AuthProvider } from "@/components/providers/auth-provider";
import { Toaster } from "@/components/ui/sonner";
import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";

const anton = Anton({ subsets: ["latin"], weight: "400", variable: "--font-display" });
const robotoSlab = Roboto_Slab({ subsets: ["latin"], variable: "--font-editorial" });
const inter = Inter({ subsets: ["latin"], variable: "--font-body" });

export const metadata: Metadata = {
  title: "CUEP",
  description: "Generación de horarios de asesorías BUAP",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={`${anton.variable} ${robotoSlab.variable} ${inter.variable} font-sans bg-background text-text`}>
        <a href="#contenido" className="skip-link">Saltar al contenido</a>
        <ThemeProvider defaultTheme="light" enableSystem={false}>
          <QueryProvider>
            <AuthProvider>
            <SiteHeader />
            <main id="contenido">{children}</main>
            <SiteFooter />
          </AuthProvider>
            </QueryProvider>
        </ThemeProvider>
        <Toaster />
      </body>
    </html>
  );
}
