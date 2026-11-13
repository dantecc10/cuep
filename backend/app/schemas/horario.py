from datetime import time

from pydantic import BaseModel, Field


class HorarioDia(BaseModel):
    dia: int = Field(ge=1, le=7)
    activo: bool
    inicio: time
    fin: time


class HorarioConfigUpdate(BaseModel):
    dias: list[HorarioDia]
