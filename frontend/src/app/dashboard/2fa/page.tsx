"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import QRCode from "react-qr-code";

export default function TwoFactorPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const [uri, setUri] = useState("");
  const [secret, setSecret] = useState("");
  const [code, setCode] = useState("");
  const [recovery, setRecovery] = useState<string[]>([]);
  const [msg, setMsg] = useState("");

  async function enroll() {
    const res = await api.post("/auth/2fa/totp/enroll", {}, { headers });
    setUri(res.data.provisioning_uri);
    setSecret(res.data.secret);
  }

  async function verify() {
    const res = await api.post("/auth/2fa/totp/verify", { code }, { headers });
    setRecovery(res.data.recovery_codes);
    setMsg("2FA activado");
  }

  async function disable() {
    await api.post("/auth/2fa/totp/disable", {}, { headers });
    setUri("");
    setSecret("");
    setRecovery([]);
    setMsg("2FA desactivado");
  }

  return (
    <div className="container-site py-10 space-y-6 max-w-2xl">
      <h1 className="font-display text-4xl uppercase text-primary">Autenticación en dos pasos</h1>
      <Card>
        <CardHeader><CardTitle>Configuración TOTP</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {!uri && <Button onClick={enroll}>Iniciar enrolamiento</Button>}
          {uri && (
            <>
              <div className="bg-white p-4 inline-block">
                <QRCode value={uri} />
              </div>
              <p className="text-xs break-all">Secreto manual: {secret}</p>
              <Input placeholder="Código de 6 dígitos" value={code} onChange={(e) => setCode(e.target.value)} />
              <Button onClick={verify}>Verificar y activar</Button>
            </>
          )}
          <Button variant="outline" onClick={disable}>Desactivar 2FA</Button>
          {msg && <p className="text-sm text-muted-foreground">{msg}</p>}
          {recovery.length > 0 && (
            <div>
              <p className="font-medium">Códigos de recuperación (guárdalos):</p>
              <ul className="text-sm font-mono">
                {recovery.map((c) => <li key={c}>{c}</li>)}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
