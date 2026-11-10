"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AppShell } from "@/components/layout/app-shell";

interface Materia { id: number; nombre: string; nivel: string; area: string; }

export default function DisponibilidadPage() {
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const { data: materias } = useQuery<Materia[]>({ queryKey: ["materias"], queryFn: async () => (await api.get("/materias", { headers })).data });

  const [days, setDays] = useState<number[]>([1]);
  const [start, setStart] = useState("08:00");
  const [end, setEnd] = useState("14:00");
  const [selected, setSelected] = useState<Record<number, { pref: number; vetada: boolean }>>({});
  const [msg, setMsg] = useState("");

  async function save() {
    if (!user) return;
    const disponibilidad = days.map((d) => ({ dia_semana: d, hora_inicio: start, hora_fin: end }));
    const materiasPayload = Object.entries(selected).map(([id, v]) => ({ materia_id: Number(id), nivel_preferencia: v.pref, vetada: v.vetada }));
    await api.put(`/tutores/${user.id}/disponibilidad`, { disponibilidad, materias: materiasPayload }, { headers });
    setMsg("Disponibilidad guardada");
  }

  return (
    <AppShell title="Disponibilidad y materias">
      <div className="space-y-6 max-w-3xl">
        <div>
          <p className="font-semibold mb-2">Días disponibles</p>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5, 6].map((d) => (
              <label key={d} className="flex items-center gap-1 text-sm">
                <input type="checkbox" checked={days.includes(d)} onChange={(e) => setDays(e.target.checked ? [...days, d] : days.filter((x) => x !== d))} />
                {d}
              </label>
            ))}
          </div>
          <div className="flex gap-2 mt-3">
            <Input type="time" value={start} onChange={(e) => setStart(e.target.value)} />
            <Input type="time" value={end} onChange={(e) => setEnd(e.target.value)} />
          </div>
        </div>
        <div>
          <p className="font-semibold mb-2">Materias</p>
          <div className="space-y-2 max-h-72 overflow-auto">
            {(materias || []).map((m) => {
              const state = selected[m.id] || { pref: 1, vetada: false };
              return (
                <div key={m.id} className="flex items-center gap-2 text-sm border border-primary rounded-card p-2">
                  <input type="checkbox" checked={!!selected[m.id]} onChange={(e) => setSelected(e.target.checked ? { ...selected, [m.id]: state } : Object.fromEntries(Object.entries(selected).filter(([k]) => Number(k) !== m.id)))} />
                  <span className="flex-1">{m.nombre}</span>
                  <select className="border border-primary rounded-button p-1 bg-surface" value={state.pref} onChange={(e) => setSelected({ ...selected, [m.id]: { ...state, pref: Number(e.target.value) } })}>
                    <option value={1}>Alta</option>
                    <option value={2}>Media</option>
                    <option value={3}>Baja</option>
                  </select>
                  <label className="flex items-center gap-1"><input type="checkbox" checked={state.vetada} onChange={(e) => setSelected({ ...selected, [m.id]: { ...state, vetada: e.target.checked } })} /> Veto</label>
                </div>
              );
            })}
          </div>
        </div>
        <Button onClick={save}>Guardar</Button>
        {msg && <p className="text-sm text-muted-foreground">{msg}</p>}
      </div>
    </AppShell>
  );
}
