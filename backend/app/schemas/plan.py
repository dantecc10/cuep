from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class PlanEstudioCreate(BaseModel):
    nombre: str
    nivel: str
    area: Optional[str] = None
    descripcion: Optional[str] = None


class PlanEstudioUpdate(BaseModel):
    nombre: Optional[str] = None
    nivel: Optional[str] = None
    area: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class PlanEstudioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    nivel: str
    area: Optional[str] = None
    descripcion: Optional[str] = None
    activo: bool = True


class PlanMateriaUpdate(BaseModel):
    materia_ids: List[int]
