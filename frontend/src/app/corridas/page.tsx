"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CorridasPage() {
  const token = useAuthStore((s) => s.token);
  const { data, isLoading } = useQuery({
    queryKey: ["corridas"],
    queryFn: async () => (await api.get("/corridas", { headers: { Authorization: `Bearer ${token}` } })).data,
    refetchInterval: 3000,
  });

  return (
    <div className="p-8 space-y-4">
      <h1 className="text-2xl font-bold">Corridas</h1>
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
  );
}
