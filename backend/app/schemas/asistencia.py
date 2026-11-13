from datetime import date, time

from pydantic import BaseModel


class SesionCreate(BaseModel):
    corrida_id: int | None = None
    sede_id: int
    grupo_id: int
    tutor_id: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    estado: str = "pendiente"
    tutor_cubridor_id: int | None = None
    comentario: str | None = None


class SesionUpdate(BaseModel):
    estado: str | None = None
    tutor_cubridor_id: int | None = None
    comentario: str | None = None
