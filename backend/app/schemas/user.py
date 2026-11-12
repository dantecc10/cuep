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
    sede_id: Optional[int] = None
    telefono: Optional[str] = None
    area_principal: Optional[str] = None
    carga_max_horas: int = 0


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    role: str
    sede_id: Optional[int] = None
    es_tutor: bool = False
    telefono: Optional[str] = None
    biografia_md: Optional[str] = None
    foto_url: Optional[str] = None
    area_principal: Optional[str] = None
    carga_max_horas: int = 0
    is_active: bool = True


class UserProfileUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    telefono: Optional[str] = None
    biografia_md: Optional[str] = None
    foto_url: Optional[str] = None
    carga_max_horas: Optional[int] = None
    area_principal: Optional[str] = None


class TeachingUpdate(BaseModel):
    enabled: bool


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    role: Optional[str] = None
    sede_id: Optional[int] = None
    es_tutor: Optional[bool] = None
    is_active: Optional[bool] = None
    telefono: Optional[str] = None
    carga_max_horas: Optional[int] = None
    area_principal: Optional[str] = None
