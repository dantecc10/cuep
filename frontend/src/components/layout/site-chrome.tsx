"use client";

import { usePathname } from "next/navigation";
import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";

const appPrefixes = ["/dashboard", "/mi-", "/verify-2fa"];

export function SiteChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isApp = appPrefixes.some((prefix) => pathname.startsWith(prefix));

  if (isApp) {
    return <main id="contenido">{children}</main>;
  }

  return (
    <>
      <SiteHeader />
      <main id="contenido">{children}</main>
      <SiteFooter />
    </>
  );
}
