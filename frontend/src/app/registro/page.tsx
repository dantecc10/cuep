"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { DualMark } from "@/components/layout/dual-mark";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Sede {
  id: number;
  nombre: string;
  ciudad: string | null;
  activo: boolean;
}

export default function RegistroPage() {
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const { data: sedes } = useQuery<Sede[]>({
    queryKey: ["sedes-public"],
    queryFn: async () => (await api.get("/sedes")).data,
  });
  const sedesActivas = (sedes || []).filter((sede) => sede.activo);

  const [form, setForm] = useState({
    email: "",
    password: "",
    nombre: "",
    apellido_paterno: "",
    apellido_materno: "",
    sede_id: 0,
    nivel: "PREPA",
    area: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!form.sede_id && sedesActivas.length > 0) {
      setForm((current) => ({ ...current, sede_id: sedesActivas[0].id }));
    }
  }, [form.sede_id, sedesActivas]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/register", form);
      const res = await api.post("/auth/login", { email: form.email, password: form.password });
      setToken(res.data.access_token);
      router.push("/mi-inscripcion");
    } catch {
      setError("No pudimos completar tu registro. Revisa tus datos e inténtalo de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container-site py-12 md:py-16">
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <section className="poster-card poster-card--paper overflow-hidden p-7 sm:p-9">
          <p className="type-kicker text-ink/70">Para aspirantes</p>
          <h1 className="mt-4 font-display text-5xl uppercase leading-[0.9] text-ink md:text-6xl">
            Tu camino a la BUAP también se construye en colectivo
          </h1>
          <p className="mt-5 font-editorial text-lg leading-relaxed text-ink/75">
            Regístrate para recibir asesorías gratuitas, consultar tu horario y formar parte de una comunidad que acompaña tu proceso.
          </p>
          <div className="mt-8 grid grid-cols-2 gap-3">
            <div className="border border-ink/25 bg-cream/60 p-3">
              <p className="type-label text-ink/45">Paso 01</p>
              <p className="mt-2 text-sm font-semibold text-ink">Crea tu cuenta</p>
            </div>
            <div className="border border-ink/25 bg-cream/60 p-3">
              <p className="type-label text-ink/45">Paso 02</p>
              <p className="mt-2 text-sm font-semibold text-ink">Elige tu sede</p>
            </div>
          </div>
          <div className="mt-6 flex items-end justify-between gap-4">
            <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={130} height={184} className="h-32 w-auto" />
            <DualMark size="sm" />
          </div>
        </section>

        <section className="poster-card p-7 sm:p-9">
          <p className="type-kicker">Registro de estudiante</p>
          <h2 className="mt-3 font-display text-4xl uppercase leading-none text-primary">Crear cuenta</h2>
          <p className="mt-3 text-sm leading-relaxed text-ink/60">Los campos marcados con * son necesarios para generar tu matrícula.</p>

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
                <Label htmlFor="sede_id">Sede *</Label>
                <select
                  id="sede_id"
                  className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                  value={form.sede_id || ""}
                  onChange={(e) => setForm({ ...form, sede_id: Number(e.target.value) })}
                  required
                >
                  <option value="" disabled>Selecciona una sede</option>
                  {sedesActivas.map((sede) => (
                    <option key={sede.id} value={sede.id}>{sede.nombre}{sede.ciudad ? ` · ${sede.ciudad}` : ""}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="nivel">Nivel *</Label>
                <select
                  id="nivel"
                  className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary"
                  value={form.nivel}
                  onChange={(e) => setForm({ ...form, nivel: e.target.value })}
                >
                  <option value="PREPA">Preparatoria</option>
                  <option value="LICENCIATURA">Licenciatura</option>
                </select>
              </div>
              {form.nivel === "LICENCIATURA" && (
                <div className="space-y-2">
                  <Label htmlFor="area">Área</Label>
                  <Input id="area" value={form.area} onChange={(e) => setForm({ ...form, area: e.target.value })} />
                </div>
              )}
            </div>

            {error && (
              <p role="alert" className="border-l-2 border-primary bg-primary/5 px-3 py-2 text-sm font-semibold text-primary">
                {error}
              </p>
            )}

            <Button type="submit" className="h-10 w-full" disabled={loading || !form.sede_id}>
              {loading ? "Creando cuenta..." : "Crear cuenta y continuar"}
            </Button>
            <p className="text-center text-xs leading-relaxed text-ink/50">
              Al registrarte aceptas participar en las actividades del colectivo. ¿Ya tienes cuenta?{" "}
              <Link href="/login" className="font-semibold text-primary underline decoration-yellow decoration-2 underline-offset-4">Inicia sesión</Link>
            </p>
          </form>
        </section>
      </div>
    </div>
  );
}
