from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Nivel = Literal["PREPA", "LICENCIATURA"]
Estatus = Literal[
    "registrado",
    "en_inscripcion",
    "inscrito",
    "activo",
    "no_asistio",
    "cancelado",
    "baja",
]
MetodoPago = Literal["efectivo", "transferencia"]


class InscripcionCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    nombre: str = Field(min_length=1, max_length=100)
    apellido_paterno: str = Field(min_length=1, max_length=100)
    apellido_materno: str | None = Field(default=None, max_length=100)
    telefono: str | None = None
    sede_id: int
    nivel: Nivel = "LICENCIATURA"
    area: str | None = Field(default=None, max_length=80)
    first_name: str | None = Field(default=None, max_length=100)
    paternal_last_name: str | None = Field(default=None, max_length=100)
    maternal_last_name: str | None = Field(default=None, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    colony: str | None = Field(default=None, max_length=150)
    municipality_state: str | None = Field(default=None, max_length=150)
    emergency_contact_raw: str | None = None
    emergency_contact_name: str | None = Field(default=None, max_length=150)
    emergency_contact_phone: str | None = Field(default=None, max_length=30)
    high_school_type: str | None = Field(default=None, max_length=20)
    exam_attempts: str | None = Field(default=None, max_length=30)
    desired_degree: str | None = Field(default=None, max_length=150)
    study_area: str | None = Field(default=None, max_length=80)
    diagnostic_exam: bool | None = None
    donation_willingness: str | None = Field(default=None, max_length=20)
    presencial_consent: bool | None = None
    credential_collected: bool | None = None
    preferred_sede_id: int | None = None
    preferred_course_location: str | None = Field(default=None, max_length=150)
    photo_url: str | None = Field(default=None, max_length=500)
    form_submitted_at: datetime | None = None
    notes: str | None = None
    solicita_simulacro: bool = False

    @field_validator("nombre", "apellido_paterno", "apellido_materno")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class RegistroResponse(BaseModel):
    id: int
    student_id: int
    email: str
    role: str
    matricula: str
    qr_token: str
    estatus: str
    anio: int
    pase_url: str


class ConfiguracionInscripcionPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    anio: int
    registro_abierto: bool
    simulacro_activo: bool
    simulacro_monto: float
    simulacro_moneda: str
    pago_efectivo_habilitado: bool
    transferencia_habilitada: bool
    transferencia_banco: str | None = None
    transferencia_titular: str | None = None
    transferencia_clabe: str | None = None
    transferencia_instrucciones: str | None = None
    parcialidades_permitidas: bool
    parcialidades_max: int
    donativo_obligatorio: bool
    donativo_descripcion: str | None = None


class ConfiguracionInscripcionUpdate(BaseModel):
    anio: int | None = Field(default=None, ge=2000, le=2100)
    registro_abierto: bool | None = None
    simulacro_activo: bool | None = None
    simulacro_monto: float | None = Field(default=None, ge=0)
    simulacro_moneda: str | None = Field(default=None, max_length=10)
    pago_efectivo_habilitado: bool | None = None
    transferencia_habilitada: bool | None = None
    transferencia_banco: str | None = Field(default=None, max_length=100)
    transferencia_titular: str | None = Field(default=None, max_length=150)
    transferencia_clabe: str | None = Field(default=None, max_length=20)
    transferencia_instrucciones: str | None = None
    parcialidades_permitidas: bool | None = None
    parcialidades_max: int | None = Field(default=None, ge=1)
    donativo_obligatorio: bool | None = None
    donativo_descripcion: str | None = None


class EventoInscripcionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    estado_anterior: str | None = None
    estado_nuevo: str | None = None
    actor_id: int | None = None
    sede_id: int | None = None
    created_at: datetime


class CargoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    anio: int
    concepto: str
    descripcion: str | None = None
    monto: float
    moneda: str
    estado: str
    fecha_limite: date | None = None


class PagoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cargo_id: int
    monto: float
    moneda: str
    metodo: str
    estado: str
    referencia: str | None = None
    comprobante_nombre: str | None = None
    fecha_pago: datetime | None = None
    validado_at: datetime | None = None
    motivo_rechazo: str | None = None
    recibo_codigo: str | None = None
    created_at: datetime


class InscripcionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None = None
    email: str | None = None
    sede_id: int | None = None
    preferred_sede_id: int | None = None
    nivel: str
    area: str | None = None
    estatus: str
    anio: int
    matricula: str | None = None
    folio: int | None = None
    qr_token: str | None = None
    registration_source: str
    checkin_at: datetime | None = None
    checkin_sede_id: int | None = None
    first_name: str | None = None
    paternal_last_name: str | None = None
    maternal_last_name: str | None = None
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    colony: str | None = None
    municipality_state: str | None = None
    emergency_contact_raw: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    high_school_type: str | None = None
    exam_attempts: str | None = None
    desired_degree: str | None = None
    study_area: str | None = None
    diagnostic_exam: bool | None = None
    donation_willingness: str | None = None
    presencial_consent: bool | None = None
    credential_collected: bool | None = None
    preferred_course_location: str | None = None
    photo_url: str | None = None
    form_submitted_at: datetime | None = None
    notes: str | None = None
    created_at: datetime


class InscripcionMe(InscripcionRead):
    cargos: list[CargoRead] = Field(default_factory=list)
    pagos: list[PagoRead] = Field(default_factory=list)
    saldo: float = 0
    pase_url: str | None = None
    eventos: list[EventoInscripcionRead] = Field(default_factory=list)


class InscripcionPage(BaseModel):
    items: list[InscripcionRead]
    total: int
    page: int
    page_size: int


class EstadoUpdate(BaseModel):
    estatus: Estatus
    motivo: str | None = None


class CheckInRequest(BaseModel):
    identificador: str = Field(min_length=1, max_length=255)
    sede_id: int | None = None


class CheckInResponse(BaseModel):
    student_id: int
    matricula: str | None = None
    nombre: str | None = None
    estatus: str
    checkin_at: datetime | None = None
    ya_registrado: bool = False
