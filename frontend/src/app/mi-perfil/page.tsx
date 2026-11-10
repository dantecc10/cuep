"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/shared/page-header";

const grupos = [
  {
    titulo: "Datos personales",
    descripcion: "Tu nombre completo como aparecerá en la credencial.",
    fields: [
      ["first_name", "Nombre"],
      ["paternal_last_name", "Apellido paterno"],
      ["maternal_last_name", "Apellido materno"],
      ["full_name", "Nombre completo"],
    ],
  },
  {
    titulo: "Contacto",
    descripcion: "Datos para localizarte y contactar a alguien en caso de emergencia.",
    fields: [
      ["phone", "Teléfono"],
      ["address", "Domicilio"],
      ["colony", "Colonia"],
      ["municipality_state", "Municipio y estado"],
      ["emergency_contact_raw", "Contacto de emergencia"],
      ["emergency_contact_name", "Nombre del contacto"],
      ["emergency_contact_phone", "Teléfono del contacto"],
    ],
  },
  {
    titulo: "Trayectoria académica",
    descripcion: "Información que nos ayuda a acompañar tu preparación.",
    fields: [
      ["high_school_type", "Prepa pública/privada"],
      ["exam_attempts", "Intentos de examen"],
      ["desired_degree", "Licenciatura deseada"],
      ["study_area", "Área"],
    ],
  },
  {
    titulo: "Preferencias y notas",
    descripcion: "Datos opcionales para organizar mejor tu participación.",
    fields: [
      ["donation_willingness", "Donativo"],
      ["preferred_course_location", "Sede preferida"],
      ["photo_url", "URL de fotografía"],
      ["notes", "Notas"],
    ],
  },
] as const;

export default function MiPerfilPage() {
  const token = useAuthStore((s) => s.token);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    (async () => {
      const h = { Authorization: `Bearer ${token}` };
      const res = await api.get("/students/me", { headers: h });
      setForm(res.data);
    })();
  }, [token]);

  async function save() {
    setSaving(true);
    setMsg("");
    try {
      await api.put("/students/me", form, { headers: { Authorization: `Bearer ${token}` } });
      setMsg("Perfil actualizado correctamente.");
    } catch {
      setMsg("No pudimos guardar los cambios. Inténtalo de nuevo.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell title="Mi perfil">
      <div className="space-y-6">
        <PageHeader title="Mi perfil" description="Completa tus datos para que el colectivo pueda acompañarte y organizar tu participación." />

        <div className="grid gap-5 lg:grid-cols-[1fr_300px] lg:items-start">
          <div className="space-y-5">
            {grupos.map((grupo) => (
              <section key={grupo.titulo} className="poster-card p-5 sm:p-6">
                <div className="border-b border-ink/15 pb-3">
                  <h2 className="font-display text-2xl uppercase text-primary">{grupo.titulo}</h2>
                  <p className="mt-1 text-sm text-ink/55">{grupo.descripcion}</p>
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {grupo.fields.map(([key, label]) => (
                    <div key={key} className="space-y-2">
                      <Label htmlFor={`perfil-${key}`}>{label}</Label>
                      <Input id={`perfil-${key}`} value={String(form[key] ?? "")} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
                    </div>
                  ))}
                </div>
              </section>
            ))}

            <section className="poster-card p-5 sm:p-6">
              <div className="border-b border-ink/15 pb-3">
                <h2 className="font-display text-2xl uppercase text-primary">Datos de acompañamiento</h2>
                <p className="mt-1 text-sm text-ink/55">Estas respuestas nos ayudan a ubicarte mejor en el colectivo.</p>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="diagnostic_exam">Examen diagnóstico</Label>
                  <select
                    id="diagnostic_exam"
                    className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                    value={String(form.diagnostic_exam ?? "")}
                    onChange={(e) => setForm({ ...form, diagnostic_exam: e.target.value === "" ? null : e.target.value === "true" })}
                  >
                    <option value="">Sin especificar</option>
                    <option value="true">Sí</option>
                    <option value="false">No</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="presencial_consent">Consentimiento presencial</Label>
                  <select
                    id="presencial_consent"
                    className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                    value={String(form.presencial_consent ?? "")}
                    onChange={(e) => setForm({ ...form, presencial_consent: e.target.value === "" ? null : e.target.value === "true" })}
                  >
                    <option value="">Sin especificar</option>
                    <option value="true">Sí</option>
                    <option value="false">No</option>
                  </select>
                </div>
              </div>
            </section>

            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={save} disabled={saving}>{saving ? "Guardando..." : "Guardar cambios"}</Button>
              {msg && <p role="status" className="text-sm font-semibold text-secondary">{msg}</p>}
            </div>
          </div>

          <aside className="space-y-4 lg:sticky lg:top-6">
            <div className="poster-card poster-card--paper p-5">
              <p className="type-label text-ink/55">Tu matrícula</p>
              <p className="mt-2 break-all font-mono text-lg font-bold text-ink">{String(form.matricula || "Por asignar")}</p>
              <p className="mt-3 text-xs leading-relaxed text-ink/60">La matrícula se genera automáticamente al registrarte y no puede editarse.</p>
            </div>
            <div className="poster-card flex items-end justify-between gap-3 p-5">
              <div>
                <p className="type-label text-ink/45">Perfil del colectivo</p>
                <p className="mt-2 font-editorial text-base font-semibold leading-snug text-ink">Tus datos nos ayudan a acompañarte mejor.</p>
              </div>
              <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={78} height={110} className="h-24 w-auto" />
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
