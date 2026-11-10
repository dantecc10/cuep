"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DualMark } from "@/components/layout/dual-mark";

export default function LoginPage() {
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/auth/login", { email, password });
      if (res.data.requires_2fa) {
        router.push(`/verify-2fa?challenge=${res.data.challenge_id}`);
        return;
      }
      setToken(res.data.access_token);
      router.push("/dashboard");
    } catch {
      setError("No pudimos iniciar sesión. Revisa tu correo y contraseña.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container-site py-12 md:py-16">
      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr] lg:items-stretch">
        <section className="poster-card poster-card--ink flex flex-col justify-between overflow-hidden p-7 sm:p-10">
          <div>
            <p className="type-kicker type-kicker--light">Sistema interno</p>
            <h1 className="mt-4 font-display text-5xl uppercase leading-[0.9] text-yellow md:text-6xl">
              Entra al colectivo
            </h1>
            <p className="mt-5 max-w-md font-editorial text-lg leading-relaxed text-paper-light/75">
              Coordina sedes, grupos, tutorías y horarios. Este espacio es para quienes sostienen el trabajo cotidiano del CUEP.
            </p>
          </div>
          <div className="mt-8 flex items-end justify-between gap-4">
            <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={150} height={212} className="h-40 w-auto sm:h-48" />
            <div className="flex flex-col items-end gap-3">
              <DualMark variant="dark" size="sm" />
              <span className="type-stamp text-yellow">Sesión segura</span>
            </div>
          </div>
        </section>

        <section className="poster-card flex items-center p-7 sm:p-10">
          <div className="w-full max-w-md">
            <p className="type-kicker">Acceso</p>
            <h2 className="mt-3 font-display text-4xl uppercase leading-none text-primary">Iniciar sesión</h2>
            <p className="mt-3 text-sm leading-relaxed text-ink/60">Usa el correo con el que te registraste en el sistema.</p>

            <form onSubmit={handleSubmit} className="mt-7 space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email">Correo electrónico</Label>
                <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Contraseña</Label>
                <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
              </div>
              {error && (
                <p role="alert" className="border-l-2 border-primary bg-primary/5 px-3 py-2 text-sm font-semibold text-primary">
                  {error}
                </p>
              )}
              <Button type="submit" className="h-10 w-full" disabled={loading}>
                {loading ? "Entrando..." : "Entrar al sistema"}
              </Button>
            </form>

            <div className="mt-7 border-t border-ink/10 pt-5 text-sm text-ink/60">
              <p>
                ¿Aún no tienes cuenta?{" "}
                <Link href="/registro" className="font-semibold text-primary underline decoration-yellow decoration-2 underline-offset-4">
                  Regístrate
                </Link>
              </p>
              <p className="mt-2">
                ¿Quieres dar asesorías?{" "}
                <Link href="/registro-tutor" className="font-semibold text-primary underline decoration-yellow decoration-2 underline-offset-4">
                  Sé tutor voluntario
                </Link>
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
