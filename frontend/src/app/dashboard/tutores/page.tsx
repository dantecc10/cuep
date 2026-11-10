"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";

interface User { id: number; nombre: string; apellido_paterno: string; email: string; es_tutor: boolean; }

export default function TutoresPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const { data } = useQuery<User[]>({ queryKey: ["tutores"], queryFn: async () => (await api.get("/tutores", { headers })).data });

  return (
    <AppShell title="Tutores">
      <div className="space-y-2">
        {(data || []).map((u) => (
          <div key={u.id} className="border border-primary bg-surface rounded-card p-3">
            <p className="font-semibold">{u.nombre} {u.apellido_paterno}</p>
            <p className="text-sm">{u.email} {u.es_tutor ? "— tutor" : ""}</p>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
