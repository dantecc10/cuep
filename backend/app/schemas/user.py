from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    role: str = "tutor"
    es_tutor: bool = False


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    role: str
    es_tutor: bool
    telefono: Optional[str] = None
    area_principal: Optional[str] = None
    carga_max_horas: int = 0
    is_active: bool = True
