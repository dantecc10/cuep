"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";
interface Student { full_name: string | null; first_name: string | null; matricula: string | null; nivel: string; study_area: string | null; area: string | null; }
import QRCode from "react-qr-code";

export default function MiCredencialPage() {
  const token = useAuthStore((s) => s.token);
  const [student, setStudent] = useState<Student | null>(null);

  useEffect(() => {
    (async () => {
      const h = { Authorization: `Bearer ${token}` };
      const res = await api.get("/students/me", { headers: h });
      setStudent(res.data);
    })();
  }, [token]);

  if (!student) return <AppShell title="Mi credencial"><p>Cargando...</p></AppShell>;

  return (
    <AppShell title="Mi credencial">
      <div className="max-w-md bg-surface border border-primary rounded-card p-6 space-y-4 poster-shadow">
        <h2 className="font-display text-3xl uppercase text-primary">{student.full_name || student.first_name}</h2>
        <p className="text-sm">Matrícula: <span className="font-mono font-bold">{student.matricula}</span></p>
        <p className="text-sm">Nivel: {student.nivel}</p>
        <p className="text-sm">Área: {student.study_area || student.area || "—"}</p>
        {student.matricula && (
          <div className="bg-white p-4 inline-block">
            <QRCode value={student.matricula} />
          </div>
        )}
      </div>
    </AppShell>
  );
}
