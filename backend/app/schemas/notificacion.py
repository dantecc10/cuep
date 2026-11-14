from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlantillaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clave: str
    nombre: str
    asunto: str
    cuerpo_texto: str
    cuerpo_html: str | None = None
    variables: list | None = None
    activo: bool
    updated_at: datetime


class PlantillaUpdate(BaseModel):
    nombre: str | None = Field(default=None, max_length=150)
    asunto: str | None = Field(default=None, max_length=255)
    cuerpo_texto: str | None = None
    cuerpo_html: str | None = None
    activo: bool | None = None


class OutboxRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plantilla_clave: str | None = None
    student_id: int | None = None
    destinatario_email: str
    asunto: str
    estado: str
    intentos: int
    ultimo_error: str | None = None
    programado_para: datetime
    enviado_at: datetime | None = None
    created_at: datetime


class OutboxPage(BaseModel):
    items: list[OutboxRead]
    total: int
    page: int
    page_size: int


class EnviarNotificacion(BaseModel):
    clave: str
    student_id: int
    dedupe_key: str | None = None
    contexto: dict | None = None
