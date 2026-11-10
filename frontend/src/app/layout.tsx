import type { Metadata } from "next";
import { Anton, Roboto_Slab, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { AuthProvider } from "@/components/providers/auth-provider";
import { Toaster } from "@/components/ui/sonner";
import { SiteChrome } from "@/components/layout/site-chrome";

const anton = Anton({ subsets: ["latin"], weight: "400", variable: "--font-display" });
const robotoSlab = Roboto_Slab({ subsets: ["latin"], variable: "--font-editorial" });
const inter = Inter({ subsets: ["latin"], variable: "--font-body" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: {
    default: "CUEP | Colectivo Universitario por la Educación Popular",
    template: "%s | CUEP",
  },
  description:
    "Colectivo Universitario por la Educación Popular: asesorías gratuitas, acompañamiento y organización comunitaria para aspirantes a la BUAP.",
  icons: { icon: "/identity/heart.png", apple: "/identity/heart.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={`${anton.variable} ${robotoSlab.variable} ${inter.variable} ${jetbrainsMono.variable} font-sans bg-background text-text`}>
        <a href="#contenido" className="skip-link">Saltar al contenido</a>
        <ThemeProvider defaultTheme="light" enableSystem={false}>
          <QueryProvider>
            <AuthProvider>
              <SiteChrome>{children}</SiteChrome>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
        <Toaster />
      </body>
    </html>
  );
}
