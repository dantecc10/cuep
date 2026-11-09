"use client";
import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function VerifyForm() {
  const params = useSearchParams();
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const challengeId = params.get("challenge") || "";
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/auth/2fa/verify", { challenge_id: challengeId, code, trust_device: false });
      setToken(res.data.access_token);
      router.push("/dashboard");
    } catch {
      setError("Código inválido o expirado");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Verificación en dos pasos</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">Te enviamos un código por correo. También puedes usar tu app autenticadora.</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="code">Código</Label>
              <Input id="code" value={code} onChange={(e) => setCode(e.target.value)} required />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Verificando..." : "Verificar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function Verify2FAPage() {
  return (
    <Suspense fallback={<div className="p-8">Cargando...</div>}>
      <VerifyForm />
    </Suspense>
  );
}
