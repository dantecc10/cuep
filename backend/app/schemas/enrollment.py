from pydantic import BaseModel, ConfigDict
from typing import Optional


class EnrollmentCreate(BaseModel):
    grupo_id: int


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    grupo_id: int
    estado: str
    payment_status: str
    student_name: Optional[str] = None
    student_matricula: Optional[str] = None
    grupo_name: Optional[str] = None
    materia_name: Optional[str] = None


class EnrollmentStatusUpdate(BaseModel):
    estado: Optional[str] = None
    payment_status: Optional[str] = None


class EnrollmentSettingsUpdate(BaseModel):
    waitlist_enabled: Optional[bool] = None
    payment_enabled: Optional[bool] = None
    payment_amount: Optional[float] = None
    payment_currency: Optional[str] = None
