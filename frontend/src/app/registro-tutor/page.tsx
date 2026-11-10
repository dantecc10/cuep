"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { DualMark } from "@/components/layout/dual-mark";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegistroTutorPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", nombre: "", apellido_paterno: "", apellido_materno: "", telefono: "" });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/auth/register-tutor", form);
      setMsg("Registro enviado. El equipo CUEP revisará tu solicitud y te contactará para activar tu perfil.");
      if (res.data?.id) setTimeout(() => router.push("/login"), 2600);
    } catch {
      setError("No pudimos enviar tu registro. Revisa tus datos e inténtalo de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container-site py-12 md:py-16">
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <section className="poster-card poster-card--ink overflow-hidden p-7 sm:p-9">
          <p className="type-kicker type-kicker--light">Para tutores</p>
          <h1 className="mt-4 font-display text-5xl uppercase leading-[0.9] text-accent md:text-6xl">
            Comparte lo que sabes, abre una puerta
          </h1>
          <p className="mt-5 font-editorial text-lg leading-relaxed text-paper-light/75">
            El CUEP se sostiene con el tiempo y los conocimientos de tutores voluntarios. Si puedes acompañar a alguien en su camino a la BUAP, este espacio es para ti.
          </p>
          <div className="mt-8 border border-paper-light/20 bg-paper-light/5 p-4">
            <p className="type-label text-accent">Cómo funciona</p>
            <p className="mt-2 text-sm leading-relaxed text-paper-light/70">
              Envías tu solicitud, el equipo de coordinación la revisa y después habilitamos tu disponibilidad y materias.
            </p>
          </div>
          <div className="mt-6 flex items-end justify-between gap-4">
            <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={130} height={184} className="h-32 w-auto" />
            <div className="flex flex-col items-end gap-3">
              <DualMark variant="dark" size="sm" />
              <span className="type-stamp text-accent">Tutoría voluntaria</span>
            </div>
          </div>
        </section>

        <section className="poster-card p-7 sm:p-9">
          <p className="type-kicker">Registro de tutor voluntario</p>
          <h2 className="mt-3 font-display text-4xl uppercase leading-none text-primary">Enviar solicitud</h2>
          <p className="mt-3 text-sm leading-relaxed text-ink/60">Tu registro queda pendiente hasta que el equipo lo apruebe.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="email">Correo electrónico *</Label>
                <Input id="email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required autoComplete="email" />
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="password">Contraseña *</Label>
                <Input id="password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required autoComplete="new-password" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre *</Label>
                <Input id="nombre" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required autoComplete="given-name" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="apellido_paterno">Apellido paterno *</Label>
                <Input id="apellido_paterno" value={form.apellido_paterno} onChange={(e) => setForm({ ...form, apellido_paterno: e.target.value })} required autoComplete="family-name" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="apellido_materno">Apellido materno</Label>
                <Input id="apellido_materno" value={form.apellido_materno} onChange={(e) => setForm({ ...form, apellido_materno: e.target.value })} autoComplete="additional-name" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="telefono">Teléfono</Label>
                <Input id="telefono" type="tel" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} autoComplete="tel" />
              </div>
            </div>

            {error && <p role="alert" className="border-l-2 border-primary bg-primary/5 px-3 py-2 text-sm font-semibold text-primary">{error}</p>}
            {msg && <p role="status" className="border-l-2 border-accent-deep bg-accent-soft px-3 py-2 text-sm font-semibold text-accent-deep">{msg}</p>}

            <Button type="submit" className="h-10 w-full" disabled={loading}>
              {loading ? "Enviando..." : "Enviar solicitud"}
            </Button>
            <p className="text-center text-xs leading-relaxed text-ink/50">
              ¿Buscas asesorías?{" "}
              <Link href="/registro" className="font-semibold text-primary underline decoration-yellow decoration-2 underline-offset-4">Regístrate como estudiante</Link>
            </p>
          </form>
        </section>
      </div>
    </div>
  );
}
