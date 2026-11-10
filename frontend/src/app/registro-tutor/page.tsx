"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegistroTutorPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", nombre: "", apellido_paterno: "", apellido_materno: "", telefono: "" });
  const [msg, setMsg] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const res = await api.post("/auth/register-tutor", form);
    setMsg("Registro enviado. Queda pendiente de aprobación por el equipo CUEP.");
    if (res.data?.id) setTimeout(() => router.push("/login"), 2000);
  }

  return (
    <div className="container-site py-12 max-w-xl">
      <h1 className="font-display text-4xl uppercase text-primary mb-4">Registro de tutor voluntario</h1>
      <form onSubmit={handleSubmit} className="bg-surface border border-primary rounded-card p-6 space-y-4 poster-shadow">
        <div className="grid gap-3 md:grid-cols-2">
          <div><Label>Email</Label><Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
          <div><Label>Contraseña</Label><Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></div>
          <div><Label>Nombre</Label><Input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} required /></div>
          <div><Label>Apellido paterno</Label><Input value={form.apellido_paterno} onChange={(e) => setForm({ ...form, apellido_paterno: e.target.value })} required /></div>
          <div><Label>Apellido materno</Label><Input value={form.apellido_materno} onChange={(e) => setForm({ ...form, apellido_materno: e.target.value })} /></div>
          <div><Label>Teléfono</Label><Input value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} /></div>
        </div>
        {msg && <p className="text-sm text-muted-foreground">{msg}</p>}
        <Button type="submit">Enviar registro</Button>
      </form>
    </div>
  );
}
