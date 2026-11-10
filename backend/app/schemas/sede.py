from pydantic import BaseModel, ConfigDict
from typing import Optional


class SedeCreate(BaseModel):
    nombre: str
    ciudad: Optional[str] = None
    codigo: str
    descripcion: Optional[str] = None
    maps_url: Optional[str] = None
    image_url: Optional[str] = None
    activo: Optional[bool] = True


class SedeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    ciudad: Optional[str] = None
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    maps_url: Optional[str] = None
    image_url: Optional[str] = None
    activo: bool = True
    waitlist_enabled: bool = True
    payment_enabled: bool = False
    payment_amount: float = 0
    payment_currency: str = "MXN"
    deleted_at: Optional[str] = None


class GrupoCreate(BaseModel):
    materia_id: int
    nombre: str
    horas_totales: int
    bloque_horas: int = 2
    capacidad: int = 30
    min_alumnos: int = 0


class GrupoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sede_id: int
    materia_id: int
    nombre: str
    horas_totales: int
    bloque_horas: int
    capacidad: int
    min_alumnos: int = 0
