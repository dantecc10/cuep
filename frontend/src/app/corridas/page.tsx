"use client";
import { AppShell } from "@/components/layout/app-shell";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CorridasPage() {
  const token = useAuthStore((s) => s.token);
  const headers = { Authorization: `Bearer ${token}` };
  const queryClient = useQueryClient();
  const [sedeId, setSedeId] = useState(1);
  const [grupoIds, setGrupoIds] = useState("1");
  const { data, isLoading } = useQuery({
    queryKey: ["corridas"],
    queryFn: async () => (await api.get("/corridas", { headers })).data,
    refetchInterval: 3000,
  });

  const createMutation = useMutation({
    mutationFn: async () => api.post("/corridas", { sede_id: sedeId, grupo_ids: grupoIds.split(",").map((x) => Number(x.trim())).filter(Boolean) }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["corridas"] }),
  });

  return (
    <AppShell title="Corridas">
      <div className="space-y-6">
      <div className="flex gap-2">
        <input className="border border-primary rounded-button p-2 bg-surface" type="number" value={sedeId} onChange={(e) => setSedeId(Number(e.target.value))} />
        <input className="border border-primary rounded-button p-2 bg-surface flex-1" placeholder="IDs de grupos, ej. 1,2" value={grupoIds} onChange={(e) => setGrupoIds(e.target.value)} />
        <button className="btn-primary" onClick={() => createMutation.mutate()}>Crear corrida</button>
      </div>
      {isLoading && <p>Cargando...</p>}
      <div className="grid gap-4">
        {(data || []).map((c: {id:number; estado:string; config_hash:string; progreso?:number; etapa?:string; metricas_optimizacion?:unknown}) => (
          <Card key={c.id}>
            <CardHeader>
              <CardTitle>Corrida #{c.id} — {c.estado}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Hash: {c.config_hash}</p>
              <p className="text-sm">Progreso: {c.progreso ?? 0}% {c.etapa ? `— ${c.etapa}` : ""}</p>
              {c.metricas_optimizacion ? (
                <pre className="mt-2 text-xs bg-muted p-2 rounded">{JSON.stringify(c.metricas_optimizacion, null, 2)}</pre>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
    </AppShell>
  );
}
