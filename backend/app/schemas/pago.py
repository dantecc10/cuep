from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.inscripcion import CargoRead, MetodoPago, PagoRead


class PagoCreate(BaseModel):
    cargo_id: int
    monto: float = Field(gt=0)
    metodo: MetodoPago
    referencia: str | None = Field(default=None, max_length=120)
    fecha_pago: datetime | None = None


class PagoValidar(BaseModel):
    aprobado: bool
    motivo: str | None = None


class ComprobanteRead(BaseModel):
    pago_id: int
    nombre: str
    content_type: str
    size: int


class PagoAdminRead(PagoRead):
    student_id: int
    matricula: str | None = None
    student_name: str | None = None
    cargo_concepto: str | None = None
    comprobante_url: str | None = None


class PagoPage(BaseModel):
    items: list[PagoAdminRead]
    total: int
    page: int
    page_size: int


class CargoCreate(BaseModel):
    student_id: int
    concepto: str = "otro"
    descripcion: str | None = None
    monto: float = Field(ge=0)
    moneda: str = "MXN"
    fecha_limite: date | None = None


class SimulacroOptInResponse(BaseModel):
    cargo: CargoRead | None = None
    creado: bool = False
