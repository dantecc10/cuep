from pydantic import BaseModel
from typing import Optional, List
from datetime import time


class DisponibilidadIn(BaseModel):
    dia_semana: int
    hora_inicio: time
    hora_fin: time


class TutorMateriaIn(BaseModel):
    materia_id: int
    nivel_preferencia: int = 1
    vetada: bool = False


class TutorUpdate(BaseModel):
    disponibilidad: Optional[List[DisponibilidadIn]] = None
    materias: Optional[List[TutorMateriaIn]] = None
    carga_max_horas: Optional[int] = None
    area_principal: Optional[str] = None
