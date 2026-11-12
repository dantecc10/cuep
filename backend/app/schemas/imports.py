from pydantic import BaseModel, Field

from typing import Optional


class ImportRowIssue(BaseModel):
    fila: int
    mensaje: str


class ImportCredential(BaseModel):
    email: str
    password_temporal: str
    email_enviado: bool


class ImportCreatedRelated(BaseModel):
    tipo: str
    nombre: str
    detalle: Optional[str] = None


class ImportReport(BaseModel):
    entidad: str
    total: int = 0
    creadas: int = 0
    omitidas: int = 0
    fallidas: int = 0
    errores: list[ImportRowIssue] = Field(default_factory=list)
    advertencias: list[ImportRowIssue] = Field(default_factory=list)
    creadas_relacionadas: list[ImportCreatedRelated] = Field(default_factory=list)
    credenciales: list[ImportCredential] = Field(default_factory=list)
    correos_enviados: int = 0
    correos_fallidos: int = 0
