"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { Button } from "@/components/ui/button";
import { DualMark } from "@/components/layout/dual-mark";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface Sede {
  id: number;
  nombre: string;
  ciudad: string | null;
  activo: boolean;
}

interface Config {
  anio: number;
  registro_abierto: boolean;
  simulacro_activo: boolean;
  simulacro_monto: number;
  simulacro_moneda: string;
  donativo_obligatorio: boolean;
  donativo_descripcion: string | null;
}

const AREAS = [
  "Ingeniería y Ciencias Exactas",
  "Ciencias Sociales",
  "Ciencias Naturales y de la Salud",
];

const STEPS = ["Cuenta", "Datos personales", "Datos académicos"];

const initialForm = {
  email: "",
  password: "",
  password_confirm: "",
  nombre: "",
  apellido_paterno: "",
  apellido_materno: "",
  telefono: "",
  sede_id: 0,
  nivel: "LICENCIATURA",
  area: "",
  address: "",
  colony: "",
  municipality_state: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  high_school_type: "",
  exam_attempts: "",
  desired_degree: "",
  study_area: "",
  diagnostic_exam: false,
  donation_willingness: "",
  presencial_consent: false,
  solicita_simulacro: false,
  notes: "",
};

function money(value: number, currency = "MXN") {
  return new Intl.NumberFormat("es-MX", { style: "currency", currency }).format(value);
}

export default function RegistroPage() {
  const router = useRouter();
  const setToken = useAuthStore((s) => s.setToken);
  const { data: sedes } = useQuery<Sede[]>({
    queryKey: ["sedes-public"],
    queryFn: async () => (await api.get("/sedes")).data,
  });
  const { data: config, isLoading: configLoading } = useQuery<Config>({
    queryKey: ["inscripcion-config-public"],
    queryFn: async () => (await api.get("/inscripciones/config")).data,
  });
  const sedesActivas = useMemo(() => (sedes || []).filter((sede) => sede.activo), [sedes]);

  const [step, setStep] = useState(0);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!form.sede_id && sedesActivas.length > 0) {
      setForm((current) => ({ ...current, sede_id: sedesActivas[0].id }));
    }
  }, [form.sede_id, sedesActivas]);

  function update<K extends keyof typeof initialForm>(key: K, value: (typeof initialForm)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function validateStep() {
    if (step === 0) {
      if (!form.email.trim() || !form.password) return "Escribe tu correo y contraseña.";
      if (form.password.length < 6) return "La contraseña debe tener al menos 6 caracteres.";
      if (form.password !== form.password_confirm) return "Las contraseñas no coinciden.";
    }
    if (step === 1) {
      if (!form.nombre.trim() || !form.apellido_paterno.trim()) {
        return "Escribe tu nombre y apellido paterno.";
      }
      if (!form.sede_id) return "Selecciona la sede donde tomarás asesorías.";
    }
    return "";
  }

  function next() {
    const message = validateStep();
    if (message) {
      setError(message);
      return;
    }
    setError("");
    setStep((current) => Math.min(current + 1, STEPS.length - 1));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const message = validateStep();
    if (message) {
      setError(message);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const payload = {
        email: form.email.trim(),
        password: form.password,
        nombre: form.nombre.trim(),
        apellido_paterno: form.apellido_paterno.trim(),
        apellido_materno: form.apellido_materno.trim() || null,
        telefono: form.telefono.trim() || null,
        sede_id: form.sede_id,
        preferred_sede_id: form.sede_id,
        nivel: form.nivel,
        area: form.area || null,
        address: form.address.trim() || null,
        colony: form.colony.trim() || null,
        municipality_state: form.municipality_state.trim() || null,
        emergency_contact_name: form.emergency_contact_name.trim() || null,
        emergency_contact_phone: form.emergency_contact_phone.trim() || null,
        high_school_type: form.high_school_type.trim() || null,
        exam_attempts: form.exam_attempts.trim() || null,
        desired_degree: form.desired_degree.trim() || null,
        study_area: form.study_area || null,
        diagnostic_exam: form.diagnostic_exam,
        donation_willingness: form.donation_willingness || null,
        presencial_consent: form.presencial_consent,
        solicita_simulacro: Boolean(config?.simulacro_activo && form.solicita_simulacro),
        notes: form.notes.trim() || null,
      };
      await api.post("/auth/register", payload);
      const response = await api.post("/auth/login", {
        email: payload.email,
        password: payload.password,
      });
      setToken(response.data.access_token);
      router.push("/mi-registro?nueva=1");
    } catch (requestError) {
      const detail =
        isAxiosError(requestError) && typeof requestError.response?.data?.detail === "string"
          ? requestError.response.data.detail
          : "No pudimos completar tu registro. Revisa tus datos e inténtalo de nuevo.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container-site py-12 md:py-16">
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <section className="poster-card poster-card--paper overflow-hidden p-7 sm:p-9">
          <p className="type-kicker text-ink/70">Para aspirantes · {config?.anio || "Nuevo ciclo"}</p>
          <h1 className="mt-4 font-display text-5xl uppercase leading-[0.9] text-ink md:text-6xl">
            Tu camino a la BUAP también se construye en colectivo
          </h1>
          <p className="mt-5 font-editorial text-lg leading-relaxed text-ink/75">
            Regístrate para recibir asesorías gratuitas, obtener tu matrícula y formar parte de
            una comunidad que acompaña tu proceso.
          </p>
          <div className="mt-8 space-y-3">
            {STEPS.map((label, index) => (
              <div
                key={label}
                className={`flex items-center gap-3 border p-3 ${
                  index === step
                    ? "border-ink bg-yellow/60"
                    : index < step
                      ? "border-ink/20 bg-cream/60"
                      : "border-ink/15 bg-cream/30"
                }`}
              >
                <span className="grid h-7 w-7 place-items-center rounded-full border border-ink font-mono text-xs font-bold">
                  {index < step ? <CheckCircle2 className="h-4 w-4" /> : String(index + 1).padStart(2, "0")}
                </span>
                <span className="text-sm font-semibold text-ink">{label}</span>
              </div>
            ))}
          </div>
          <div className="mt-6 flex items-end justify-between gap-4">
            <Image src="/identity/penguin.png" alt="Pingüino del CUEP" width={130} height={184} className="h-32 w-auto" />
            <DualMark size="sm" />
          </div>
        </section>

        <section className="poster-card p-7 sm:p-9">
          {configLoading ? (
            <div className="space-y-3">
              <div className="h-5 w-40 animate-pulse bg-ink/10" />
              <div className="h-12 w-full animate-pulse bg-ink/10" />
              <div className="h-12 w-full animate-pulse bg-ink/10" />
            </div>
          ) : config && !config.registro_abierto ? (
            <div className="py-10">
              <p className="type-kicker">Registro cerrado</p>
              <h2 className="mt-3 font-display text-4xl uppercase leading-none text-primary">
                El registro {config.anio} está cerrado
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-ink/65">
                Si ya tienes cuenta, puedes iniciar sesión para consultar tu matrícula y pase. Si
                necesitas apoyo, acércate a tu sede.
              </p>
              <Link href="/login" className="btn-primary mt-6 inline-flex">Iniciar sesión</Link>
            </div>
          ) : (
            <>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="type-kicker">Registro de aspirante</p>
                  <h2 className="mt-2 font-display text-4xl uppercase leading-none text-primary">
                    {STEPS[step]}
                  </h2>
                </div>
                <span className="font-mono text-xs font-bold text-ink/35">
                  {String(step + 1).padStart(2, "0")} / {String(STEPS.length).padStart(2, "0")}
                </span>
              </div>

              <form onSubmit={handleSubmit} className="mt-6 space-y-5">
                {step === 0 ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="email">Correo electrónico *</Label>
                      <Input id="email" type="email" className="h-10" value={form.email} onChange={(event) => update("email", event.target.value)} required autoComplete="email" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="password">Contraseña *</Label>
                      <Input id="password" type="password" className="h-10" value={form.password} onChange={(event) => update("password", event.target.value)} required minLength={6} autoComplete="new-password" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="password_confirm">Confirmar contraseña *</Label>
                      <Input id="password_confirm" type="password" className="h-10" value={form.password_confirm} onChange={(event) => update("password_confirm", event.target.value)} required minLength={6} autoComplete="new-password" />
                    </div>
                    <p className="text-xs leading-relaxed text-ink/50 sm:col-span-2">
                      Usa un correo al que puedas acceder: ahí enviaremos tu confirmación y avisos
                      del proceso. La contraseña debe tener al menos 6 caracteres.
                    </p>
                  </div>
                ) : null}

                {step === 1 ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="nombre">Nombre(s) *</Label>
                      <Input id="nombre" className="h-10" value={form.nombre} onChange={(event) => update("nombre", event.target.value)} required autoComplete="given-name" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apellido_paterno">Apellido paterno *</Label>
                      <Input id="apellido_paterno" className="h-10" value={form.apellido_paterno} onChange={(event) => update("apellido_paterno", event.target.value)} required autoComplete="family-name" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="apellido_materno">Apellido materno</Label>
                      <Input id="apellido_materno" className="h-10" value={form.apellido_materno} onChange={(event) => update("apellido_materno", event.target.value)} autoComplete="additional-name" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="telefono">Teléfono</Label>
                      <Input id="telefono" type="tel" className="h-10" value={form.telefono} onChange={(event) => update("telefono", event.target.value)} autoComplete="tel" placeholder="222 000 0000" />
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="sede_id">Sede *</Label>
                      <select id="sede_id" className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary" value={form.sede_id || ""} onChange={(event) => update("sede_id", Number(event.target.value))} required>
                        <option value="" disabled>Selecciona una sede</option>
                        {sedesActivas.map((sede) => (
                          <option key={sede.id} value={sede.id}>{sede.nombre}{sede.ciudad ? ` · ${sede.ciudad}` : ""}</option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="address">Calle y número</Label>
                      <Input id="address" className="h-10" value={form.address} onChange={(event) => update("address", event.target.value)} autoComplete="street-address" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="colony">Colonia</Label>
                      <Input id="colony" className="h-10" value={form.colony} onChange={(event) => update("colony", event.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="municipality_state">Municipio y estado</Label>
                      <Input id="municipality_state" className="h-10" value={form.municipality_state} onChange={(event) => update("municipality_state", event.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="emergency_contact_name">Contacto de emergencia</Label>
                      <Input id="emergency_contact_name" className="h-10" value={form.emergency_contact_name} onChange={(event) => update("emergency_contact_name", event.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="emergency_contact_phone">Teléfono de emergencia</Label>
                      <Input id="emergency_contact_phone" type="tel" className="h-10" value={form.emergency_contact_phone} onChange={(event) => update("emergency_contact_phone", event.target.value)} />
                    </div>
                  </div>
                ) : null}

                {step === 2 ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="nivel">Nivel *</Label>
                      <select id="nivel" className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary" value={form.nivel} onChange={(event) => update("nivel", event.target.value)}>
                        <option value="PREPA">Preparatoria</option>
                        <option value="LICENCIATURA">Licenciatura</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="area">Área de interés</Label>
                      <select id="area" className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary" value={form.area} onChange={(event) => update("area", event.target.value)}>
                        <option value="">Selecciona un área</option>
                        {AREAS.map((area) => <option key={area} value={area}>{area}</option>)}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="high_school_type">Bachillerato de origen</Label>
                      <Input id="high_school_type" className="h-10" value={form.high_school_type} onChange={(event) => update("high_school_type", event.target.value)} placeholder="BUAP, CBTIS, CONALEP..." />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="exam_attempts">Intento de examen</Label>
                      <select id="exam_attempts" className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary" value={form.exam_attempts} onChange={(event) => update("exam_attempts", event.target.value)}>
                        <option value="">Selecciona una opción</option>
                        <option value="Primera vez">Primera vez</option>
                        <option value="Segunda vez">Segunda vez</option>
                        <option value="Tercera o más">Tercera o más</option>
                      </select>
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="desired_degree">Carrera o programa deseado</Label>
                      <Input id="desired_degree" className="h-10" value={form.desired_degree} onChange={(event) => update("desired_degree", event.target.value)} />
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="study_area">Área de estudio</Label>
                      <select id="study_area" className="h-10 w-full border border-ink/30 bg-surface px-3 text-sm text-ink outline-none focus-visible:border-primary" value={form.study_area} onChange={(event) => update("study_area", event.target.value)}>
                        <option value="">Selecciona un área</option>
                        {AREAS.map((area) => <option key={area} value={area}>{area}</option>)}
                      </select>
                    </div>

                    <label className="flex items-start gap-3 border border-ink/20 bg-sand/40 p-3 text-sm sm:col-span-2">
                      <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[#A92730]" checked={form.presencial_consent} onChange={(event) => update("presencial_consent", event.target.checked)} />
                      <span>Autorizo mi participación en las actividades presenciales del CUEP.</span>
                    </label>

                    {config?.simulacro_activo ? (
                      <label className="flex items-start gap-3 border border-ink bg-yellow/40 p-4 text-sm sm:col-span-2">
                        <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[#A92730]" checked={form.solicita_simulacro} onChange={(event) => update("solicita_simulacro", event.target.checked)} />
                        <span>
                          <span className="block font-semibold text-ink">
                            Quiero participar en el simulacro ({money(config.simulacro_monto, config.simulacro_moneda)}).
                          </span>
                          <span className="mt-1 block text-xs leading-relaxed text-ink/60">
                            Es opcional, no bloquea tu inscripción y podrás pagarlo después
                            desde Mis pagos.
                          </span>
                        </span>
                      </label>
                    ) : null}

                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="notes">¿Algo que debamos saber?</Label>
                      <textarea id="notes" rows={3} className="w-full border border-ink/30 bg-surface px-3 py-2 text-sm text-ink outline-none focus-visible:border-primary" value={form.notes} onChange={(event) => update("notes", event.target.value)} />
                    </div>
                  </div>
                ) : null}

                {error ? (
                  <p role="alert" className="border-l-2 border-primary bg-primary/5 px-3 py-2 text-sm font-semibold text-primary">
                    {error}
                  </p>
                ) : null}

                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  {step > 0 ? (
                    <Button type="button" variant="outline" onClick={() => { setError(""); setStep((current) => current - 1); }}>
                      <ArrowLeft className="mr-2 h-4 w-4" /> Atrás
                    </Button>
                  ) : (
                    <span />
                  )}
                  {step < STEPS.length - 1 ? (
                    <Button type="button" onClick={next}>
                      Continuar <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  ) : (
                    <Button type="submit" disabled={loading || !form.sede_id}>
                      {loading ? "Creando cuenta..." : "Crear cuenta y continuar"}
                    </Button>
                  )}
                </div>

                <p className="text-center text-xs leading-relaxed text-ink/50">
                  ¿Ya tienes cuenta?{" "}
                  <Link href="/login" className="font-semibold text-primary underline decoration-yellow decoration-2 underline-offset-4">
                    Inicia sesión
                  </Link>
                </p>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
