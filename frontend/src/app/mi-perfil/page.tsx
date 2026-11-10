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
import { FotoUploader } from "@/components/shared/foto-uploader";

const studentGroups = [
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
      ["notes", "Notas"],
    ],
  },
] as const;

const staffGroups = [
  {
    titulo: "Datos personales",
    descripcion: "La información que aparece en tu perfil del colectivo.",
    fields: [
      ["nombre", "Nombre"],
      ["apellido_paterno", "Apellido paterno"],
      ["apellido_materno", "Apellido materno"],
      ["telefono", "Teléfono"],
      ["area_principal", "Área principal"],
      ["carga_max_horas", "Carga máxima de horas"],
    ],
  },
] as const;

const roleLabels: Record<string, string> = {
  admin: "Administración",
  coordinador: "Coordinación",
  subcoordinador: "Subcoordinación",
  tutor: "Tutoría",
  alumno: "Estudiante",
};

export default function MiPerfilPage() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const role = user?.role;
  const isStudent = role === "alumno";
  const photoKey = isStudent ? "photo_url" : "foto_url";
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || !role) return;
    let cancelled = false;

    (async () => {
      setLoading(true);
      setMsg("");
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const res = await api.get(isStudent ? "/students/me" : "/auth/me", { headers });
        if (!cancelled) setForm(res.data);
      } catch {
        if (!cancelled) setMsg("No pudimos cargar tu perfil. Intenta recargar la página.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token, role, isStudent]);

  async function save() {
    setSaving(true);
    setMsg("");
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const endpoint = isStudent ? "/students/me" : "/auth/me/profile";
      await api.put(endpoint, form, { headers });
      setMsg("Perfil actualizado correctamente.");
    } catch {
      setMsg("No pudimos guardar los cambios. Revisa los datos e inténtalo de nuevo.");
    } finally {
      setSaving(false);
    }
  }

  function setField(key: string, raw: string) {
    setForm((current) => ({
      ...current,
      [key]: key === "carga_max_horas" ? (raw === "" ? null : Number(raw)) : raw,
    }));
  }

  if (loading || !role) {
    return (
      <AppShell title="Mi perfil">
        <div className="space-y-4">
          <PageHeader title="Mi perfil" description="Cargando tu información..." />
          <div className="h-48 animate-pulse border border-ink/15 bg-sand" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="Mi perfil">
      <div className="space-y-6">
        <PageHeader title="Mi perfil" description="Actualiza tus datos, tu fotografía y la información que compartes con el colectivo." />

        <div className="grid gap-5 lg:grid-cols-[1fr_300px] lg:items-start">
          <div className="space-y-5">
            <section className="poster-card p-5 sm:p-6">
              <div className="border-b border-ink/15 pb-3">
                <h2 className="font-display text-2xl uppercase text-primary">Fotografía</h2>
                <p className="mt-1 text-sm text-ink/55">Puedes subir una imagen o usar una URL pública si el almacenamiento no está configurado.</p>
              </div>
              <div className="mt-4">
                <FotoUploader
                  value={String(form[photoKey] ?? "")}
                  onChange={(url) => setForm((current) => ({ ...current, [photoKey]: url }))}
                  label="Fotografía de perfil"
                  id="perfil-foto"
                />
              </div>
            </section>

            {(isStudent ? studentGroups : staffGroups).map((grupo) => (
              <section key={grupo.titulo} className="poster-card p-5 sm:p-6">
                <div className="border-b border-ink/15 pb-3">
                  <h2 className="font-display text-2xl uppercase text-primary">{grupo.titulo}</h2>
                  <p className="mt-1 text-sm text-ink/55">{grupo.descripcion}</p>
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {grupo.fields.map(([key, label]) => (
                    <div key={key} className="space-y-2">
                      <Label htmlFor={`perfil-${key}`}>{label}</Label>
                      <Input
                        id={`perfil-${key}`}
                        type={key === "carga_max_horas" ? "number" : "text"}
                         min={key === "carga_max_horas" ? 0 : undefined}
                        value={String(form[key] ?? "")}
                        onChange={(e) => setField(key, e.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </section>
            ))}

            {!isStudent && (
              <section className="poster-card p-5 sm:p-6">
                <div className="border-b border-ink/15 pb-3">
                  <h2 className="font-display text-2xl uppercase text-primary">Sobre ti</h2>
                  <p className="mt-1 text-sm text-ink/55">Una breve presentación para el equipo del colectivo.</p>
                </div>
                <div className="mt-4 space-y-2">
                  <Label htmlFor="perfil-biografia">Biografía</Label>
                  <textarea
                    id="perfil-biografia"
                    className="min-h-32 w-full border border-ink/30 bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:border-primary"
                    value={String(form.biografia_md ?? "")}
                    onChange={(e) => setField("biografia_md", e.target.value)}
                  />
                </div>
              </section>
            )}

            {isStudent && (
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
            )}

            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={save} disabled={saving}>{saving ? "Guardando..." : "Guardar cambios"}</Button>
              {msg && <p role="status" className="text-sm font-semibold text-secondary">{msg}</p>}
            </div>
          </div>

          <aside className="space-y-4 lg:sticky lg:top-6">
            <div className="poster-card poster-card--paper p-5">
              {isStudent ? (
                <>
                  <p className="type-label text-ink/55">Tu matrícula</p>
                  <p className="mt-2 break-all font-mono text-lg font-bold text-ink">{String(form.matricula || "Por asignar")}</p>
                  <p className="mt-3 text-xs leading-relaxed text-ink/60">La matrícula se genera automáticamente al registrarte y no puede editarse.</p>
                </>
              ) : (
                <>
                  <p className="type-label text-ink/55">Tu rol en el colectivo</p>
                  <p className="mt-2 font-display text-2xl uppercase text-primary">{roleLabels[role] || role}</p>
                  <p className="mt-3 text-xs leading-relaxed text-ink/60">Área: {String(form.area_principal || "Sin especificar")}</p>
                  <p className="mt-1 text-xs leading-relaxed text-ink/60">Carga máxima: {String(form.carga_max_horas || 0)} horas</p>
                </>
              )}
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
