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
    nivel: str = "LICENCIATURA"
    area: Optional[str] = None
    first_name: Optional[str] = None
    paternal_last_name: Optional[str] = None
    maternal_last_name: Optional[str] = None
    full_name: Optional[str] = None
    address: Optional[str] = None
    colony: Optional[str] = None
    municipality_state: Optional[str] = None
    emergency_contact_raw: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    high_school_type: Optional[str] = None
    exam_attempts: Optional[str] = None
    desired_degree: Optional[str] = None
    study_area: Optional[str] = None
    diagnostic_exam: Optional[bool] = None
    donation_willingness: Optional[str] = None
    presencial_consent: Optional[bool] = None
    credential_collected: Optional[bool] = None
    preferred_sede_id: Optional[int] = None
    preferred_course_location: Optional[str] = None
    photo_url: Optional[str] = None
    form_submitted_at: Optional[str] = None
    notes: Optional[str] = None


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int] = None
    email: Optional[str] = None
    sede_id: Optional[int] = None
    preferred_sede_id: Optional[int] = None
    nivel: str
    area: Optional[str] = None
    estatus: str

    first_name: Optional[str] = None
    paternal_last_name: Optional[str] = None
    maternal_last_name: Optional[str] = None
    full_name: Optional[str] = None

    address: Optional[str] = None
    colony: Optional[str] = None
    municipality_state: Optional[str] = None
    phone: Optional[str] = None

    emergency_contact_raw: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    high_school_type: Optional[str] = None
    exam_attempts: Optional[str] = None
    desired_degree: Optional[str] = None
    study_area: Optional[str] = None
    diagnostic_exam: Optional[bool] = None
    donation_willingness: Optional[str] = None
    presencial_consent: Optional[bool] = None
    credential_collected: Optional[bool] = None

    preferred_course_location: Optional[str] = None
    photo_url: Optional[str] = None

    folio: Optional[int] = None
    matricula: Optional[str] = None
    form_submitted_at: Optional[str] = None
    notes: Optional[str] = None


class StudentUpdate(BaseModel):
    sede_id: Optional[int] = None
    preferred_sede_id: Optional[int] = None
    nivel: Optional[str] = None
    area: Optional[str] = None
    estatus: Optional[str] = None
    first_name: Optional[str] = None
    paternal_last_name: Optional[str] = None
    maternal_last_name: Optional[str] = None
    full_name: Optional[str] = None
    address: Optional[str] = None
    colony: Optional[str] = None
    municipality_state: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_raw: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    high_school_type: Optional[str] = None
    exam_attempts: Optional[str] = None
    desired_degree: Optional[str] = None
    study_area: Optional[str] = None
    diagnostic_exam: Optional[bool] = None
    donation_willingness: Optional[str] = None
    presencial_consent: Optional[bool] = None
    credential_collected: Optional[bool] = None
    preferred_course_location: Optional[str] = None
    photo_url: Optional[str] = None
    notes: Optional[str] = None
