from pydantic import BaseModel, ConfigDict
from typing import Optional


class MateriaCreate(BaseModel):
    nombre: str
    nivel: str
    area: str
    descripcion: Optional[str] = None


class MateriaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    nivel: str
    area: str
    descripcion: Optional[str] = None
