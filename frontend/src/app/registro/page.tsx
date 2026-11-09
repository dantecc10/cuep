"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function RegistroPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: "", password: "", nombre: "", apellido_paterno: "", apellido_materno: "",
    sede_id: 1, nivel: "PREPA", area: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/register", form);
      const res = await api.post("/auth/login", { email: form.email, password: form.password });
      localStorage.setItem("cuep_token", res.data.access_token);
      router.push("/mi-inscripcion");
    } catch {
      setError("No se pudo registrar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader><CardTitle>Registro de estudiante</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Email</Label><Input value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})} required /></div>
              <div><Label>Contraseña</Label><Input type="password" value={form.password} onChange={(e)=>setForm({...form,password:e.target.value})} required /></div>
              <div><Label>Nombre</Label><Input value={form.nombre} onChange={(e)=>setForm({...form,nombre:e.target.value})} required /></div>
              <div><Label>Apellido paterno</Label><Input value={form.apellido_paterno} onChange={(e)=>setForm({...form,apellido_paterno:e.target.value})} required /></div>
              <div><Label>Apellido materno</Label><Input value={form.apellido_materno} onChange={(e)=>setForm({...form,apellido_materno:e.target.value})} /></div>
              <div><Label>Sede ID</Label><Input type="number" value={form.sede_id} onChange={(e)=>setForm({...form,sede_id:Number(e.target.value)})} required /></div>
              <div><Label>Nivel</Label>
                <select className="w-full border rounded p-2" value={form.nivel} onChange={(e)=>setForm({...form,nivel:e.target.value})}>
                  <option value="PREPA">Prepa</option>
                  <option value="LICENCIATURA">Licenciatura</option>
                </select>
              </div>
              {form.nivel === "LICENCIATURA" && (
                <div><Label>Área</Label><Input value={form.area} onChange={(e)=>setForm({...form,area:e.target.value})} /></div>
              )}
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>{loading ? "Registrando..." : "Registrarse"}</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
