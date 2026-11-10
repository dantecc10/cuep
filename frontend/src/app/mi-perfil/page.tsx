"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell } from "@/components/layout/app-shell";

export default function MiPerfilPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [msg, setMsg] = useState("");

  useEffect(() => {
    (async () => {
      const h = { Authorization: `Bearer ${token}` };
      const res = await api.get("/students/me", { headers: h });
      setForm(res.data);
    })();
  }, [token]);

  async function save() {
    await api.put("/students/me", form, { headers });
    setMsg("Perfil actualizado");
  }

  const fields = [
    ["first_name", "Nombre"],
    ["paternal_last_name", "Apellido paterno"],
    ["maternal_last_name", "Apellido materno"],
    ["full_name", "Nombre completo"],
    ["phone", "Teléfono"],
    ["address", "Domicilio"],
    ["colony", "Colonia"],
    ["municipality_state", "Municipio y estado"],
    ["emergency_contact_raw", "Contacto de emergencia"],
    ["emergency_contact_name", "Nombre del contacto"],
    ["emergency_contact_phone", "Teléfono del contacto"],
    ["high_school_type", "Prepa pública/privada"],
    ["exam_attempts", "Intentos de examen"],
    ["desired_degree", "Licenciatura deseada"],
    ["study_area", "Área"],
    ["donation_willingness", "Donativo"],
    ["preferred_course_location", "Sede preferida"],
    ["photo_url", "URL de fotografía"],
    ["notes", "Notas"],
  ];

  return (
    <AppShell title="Mi perfil">
      <div className="space-y-4 max-w-3xl">
        <div className="grid gap-3 md:grid-cols-2">
          {fields.map(([key, label]) => (
            <div key={key}>
              <Label>{label}</Label>
              <Input value={String(form[key] ?? "")} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
            </div>
          ))}
          <div>
            <Label>Examen diagnóstico</Label>
            <select className="w-full border border-primary rounded-button p-2 bg-surface" value={String(form.diagnostic_exam ?? "")} onChange={(e) => setForm({ ...form, diagnostic_exam: e.target.value === "true" })}>
              <option value="">Sin especificar</option>
              <option value="true">Sí</option>
              <option value="false">No</option>
            </select>
          </div>
          <div>
            <Label>Consentimiento presencial</Label>
            <select className="w-full border border-primary rounded-button p-2 bg-surface" value={String(form.presencial_consent ?? "")} onChange={(e) => setForm({ ...form, presencial_consent: e.target.value === "true" })}>
              <option value="">Sin especificar</option>
              <option value="true">Sí</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>
        {form.matricula ? <p className="font-semibold">Matrícula: {String(form.matricula)}</p> : null}
        {msg && <p className="text-sm text-muted-foreground">{msg}</p>}
        <Button onClick={save}>Guardar</Button>
      </div>
    </AppShell>
  );
}
