"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Image from "next/image";
import { PosterFrame } from "@/components/layout/poster-frame";

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
      setError("Credenciales inválidas");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container-site py-12 grid gap-8 md:grid-cols-2 items-center">
      <PosterFrame title="Inicia sesión" subtitle="Acceso al sistema CUEP" imageSrc="/identity/megaphone.svg" />
      <div className="flex justify-center mb-2">
        <Image src="/identity/penguin.png" alt="Pingüino CUEP" width={72} height={102} />
      </div>
      <form onSubmit={handleSubmit} className="bg-surface border border-primary rounded-card p-6 space-y-4 poster-shadow">
        <h2 className="font-display text-3xl uppercase text-primary">Iniciar sesión</h2>
        <div className="space-y-2">
          <Label htmlFor="email">Correo electrónico</Label>
          <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Contraseña</Label>
          <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className="text-sm text-primary font-semibold">{error}</p>}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"}
        </Button>
      </form>
    </div>
  );
}
