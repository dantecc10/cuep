"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import QRCode from "react-qr-code";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";

interface Student {
  full_name: string | null;
  first_name: string | null;
  matricula: string | null;
  nivel: string;
  study_area: string | null;
  area: string | null;
}

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

  if (!student) {
    return (
      <AppShell title="Mi credencial">
        <div className="poster-card p-8">
          <p className="type-label text-ink/40">Credencial</p>
          <p className="mt-2 font-editorial text-lg text-ink/60">Cargando tu credencial del colectivo...</p>
        </div>
      </AppShell>
    );
  }

  const nombre = student.full_name || student.first_name || "Estudiante CUEP";

  return (
    <AppShell title="Mi credencial">
      <div className="space-y-6">
        <PageHeader title="Mi credencial" description="Tu identificación como estudiante del colectivo. Preséntala en tu sede cuando se te solicite." />

        <div className="grid gap-5 lg:grid-cols-[minmax(0,560px)_1fr] lg:items-start">
          <article className="relative overflow-hidden border-[1.5px] border-ink bg-surface shadow-[8px_8px_0_#A92730]">
            <div className="flex items-center justify-between border-b-[1.5px] border-ink bg-primary px-5 py-4 text-white">
              <div className="flex items-center gap-3">
                <Image src="/identity/heart.png" alt="" width={30} height={30} className="h-8 w-8" />
                <div>
                  <p className="font-display text-2xl uppercase leading-none">CUEP</p>
                  <p className="mt-1 font-mono text-[0.55rem] uppercase tracking-[0.14em] text-white/70">Credencial de estudiante</p>
                </div>
              </div>
              <span className="type-stamp border-white/60 text-white">Vigente</span>
            </div>

            <div className="grid gap-5 p-5 sm:grid-cols-[1fr_132px] sm:p-6">
              <div>
                <p className="type-label text-ink/40">Nombre</p>
                <h2 className="mt-1 font-display text-3xl uppercase leading-none text-ink">{nombre}</h2>

                <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-ink/15 pt-4">
                  <div>
                    <dt className="type-label text-ink/40">Matrícula</dt>
                    <dd className="mt-1 font-mono text-sm font-bold text-primary">{student.matricula || "Por asignar"}</dd>
                  </div>
                  <div>
                    <dt className="type-label text-ink/40">Nivel</dt>
                    <dd className="mt-1 text-sm font-semibold text-ink">{student.nivel === "PREPA" ? "Preparatoria" : "Licenciatura"}</dd>
                  </div>
                  <div className="col-span-2">
                    <dt className="type-label text-ink/40">Área</dt>
                    <dd className="mt-1 text-sm font-semibold text-ink">{student.study_area || student.area || "Sin especificar"}</dd>
                  </div>
                </dl>
              </div>

              <div className="flex flex-col items-center gap-3">
                <div className="border-[1.5px] border-ink bg-white p-3">
                  {student.matricula ? <QRCode value={student.matricula} size={96} /> : <div className="grid h-24 w-24 place-items-center bg-sand text-center font-mono text-[0.55rem] uppercase text-ink/50">Sin código</div>}
                </div>
                <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={70} height={99} className="h-20 w-auto" />
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-ink/15 bg-sand/60 px-5 py-3">
              <p className="font-mono text-[0.55rem] uppercase tracking-[0.12em] text-ink/50">Colectivo Universitario por la Educación Popular</p>
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 rotate-6 place-items-center border border-ink bg-paper shadow-[2px_2px_0_#E8B83E]">
                  <Image src="/identity/fist.svg" alt="" width={18} height={18} className="h-4 w-4" unoptimized />
                </span>
                <p className="font-editorial text-sm font-semibold text-primary">BUAP</p>
              </div>
            </div>
          </article>

          <aside className="poster-card poster-card--paper p-5">
            <p className="type-label text-ink/55">Cómo usarla</p>
            <h3 className="mt-2 font-display text-2xl uppercase text-ink">Tu identidad en el colectivo</h3>
            <ul className="mt-4 space-y-3 font-editorial text-sm leading-relaxed text-ink/70">
              <li>Preséntala cuando acudas a una sede o actividad del CUEP.</li>
              <li>Tu matrícula es única y no cambia; guárdala para cualquier trámite.</li>
              <li>Si algún dato es incorrecto, actualiza tu perfil y avisa a coordinación.</li>
            </ul>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
