from pydantic import BaseModel, ConfigDict
from typing import Optional


class StudentRegister(BaseModel):
    email: str
    password: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    telefono: Optional[str] = None
    sede_id: int
    nivel: str
    area: Optional[str] = None


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    sede_id: int
    nivel: str
    area: Optional[str] = None
    estatus: str


class StudentUpdate(BaseModel):
    sede_id: Optional[int] = None
    nivel: Optional[str] = None
    area: Optional[str] = None
    estatus: Optional[str] = None
