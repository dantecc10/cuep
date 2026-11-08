"use client";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const logout = useAuthStore((s) => s.logout);
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Dashboard CUEP</h1>
      <p className="text-muted-foreground mb-4">Base frontend lista. Conecta con la API en /api/v1.</p>
      <Button onClick={logout} variant="outline">Cerrar sesión</Button>
    </div>
  );
}
