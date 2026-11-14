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
  registrado: "Registrado",
  en_inscripcion: "En inscripción",
  inscrito: "Inscrito",
  activo: "Activo",
  no_asistio: "No asistió",
  baja: "Baja",
  pagado: "Pagado",
  parcial: "Parcial",
  validado: "Validado",
  rechazado: "Rechazado",
  enviado: "Enviado",
  simulado: "Simulado",
  exento: "Exento",
};

export function StatusBadge({ status }: { status: string }) {
  const label = labels[status] || status;
  const positive = ["COMPLETADO", "confirmada", "PUBLICADA", "asistio", "cubierta", "aprobada", "inscrito", "activo", "pagado", "validado", "enviado", "exento"];
  const negative = ["ERROR", "cancelada", "falta", "no_asistio", "cancelado", "baja", "rechazado"];
  const variant = negative.includes(status) ? "destructive" : positive.includes(status) ? "accent" : "secondary";
  return <Badge variant={variant as "default" | "secondary" | "accent" | "destructive"}>{label}</Badge>;
}
