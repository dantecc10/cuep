from datetime import time

from pydantic import BaseModel, Field


class HorarioDia(BaseModel):
    dia_semana: int = Field(ge=1, le=7)
    activo: bool
    hora_inicio: time
    hora_fin: time


class HorarioConfigUpdate(BaseModel):
    dias: list[HorarioDia]
