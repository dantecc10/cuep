"use client";
import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import { api } from "@/lib/api";

interface Sede { id: number; nombre: string; ciudad: string | null; descripcion: string | null; image_url: string | null; maps_url: string | null; activo: boolean; }

export default function SedesPage() {
  const { data } = useQuery<Sede[]>({ queryKey: ["sedes-public"], queryFn: async () => (await api.get("/sedes")).data });

  return (
    <div className="container-site py-10 space-y-6">
      <h1 className="font-display text-4xl uppercase text-primary">Sedes</h1>
      <div className="grid gap-4 md:grid-cols-3">
        {(data || []).filter((s) => s.activo).map((sede) => (
          <article key={sede.id} className="bg-surface border border-primary rounded-card p-5 poster-shadow space-y-3">
            {sede.image_url && <Image src={sede.image_url} alt={sede.nombre} width={400} height={220} className="w-full h-40 object-cover rounded-card" />}
            <h2 className="font-display text-2xl uppercase text-primary">{sede.nombre}</h2>
            {sede.ciudad && <p className="text-sm font-semibold">{sede.ciudad}</p>}
            {sede.descripcion && <p className="text-sm">{sede.descripcion}</p>}
            {sede.maps_url && <a href={sede.maps_url} target="_blank" rel="noreferrer" className="btn-primary inline-flex">Ver en Google Maps</a>}
          </article>
        ))}
      </div>
    </div>
  );
}
