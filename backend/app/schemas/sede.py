from pydantic import BaseModel, ConfigDict


class SedeCreate(BaseModel):
    nombre: str


class SedeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class GrupoCreate(BaseModel):
    materia_id: int
    nombre: str
    horas_totales: int
    bloque_horas: int = 2
    capacidad: int = 1


class GrupoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sede_id: int
    materia_id: int
    nombre: str
    horas_totales: int
    bloque_horas: int
    capacidad: int
