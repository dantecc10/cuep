import { Badge } from "@/components/ui/badge";

const labels: Record<string, string> = {
  PENDIENTE: "Pendiente",
  PROCESANDO: "Procesando",
  COMPLETADO: "Completado",
  APROBADA: "Aprobada",
  PUBLICADA: "Publicada",
  ERROR: "Error",
  confirmada: "Confirmada",
  pendiente_pago: "Pendiente de pago",
  lista_espera: "Lista de espera",
  cancelada: "Cancelada",
  pendiente: "Pendiente",
  asistio: "Asistió",
  retardo: "Retardo",
  falta: "Falta",
  justificada: "Justificada",
  cubierta: "Cubierta",
};

export function StatusBadge({ status }: { status: string }) {
  const label = labels[status] || status;
  const variant = status === "ERROR" || status === "cancelada" || status === "falta" ? "destructive" : status === "COMPLETADO" || status === "confirmada" || status === "PUBLICADA" || status === "asistio" || status === "cubierta" || status === "aprobada" ? "accent" : "secondary";
  return <Badge variant={variant as "default" | "secondary" | "accent" | "destructive"}>{label}</Badge>;
}
