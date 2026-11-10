from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    sede_id: Mapped[int | None] = mapped_column(ForeignKey("sedes.id", ondelete="SET NULL"))
    preferred_sede_id: Mapped[int | None] = mapped_column(ForeignKey("sedes.id", ondelete="SET NULL"))
    nivel: Mapped[str] = mapped_column(String(20), nullable=False, default="LICENCIATURA")
    area: Mapped[str | None] = mapped_column(String(80))
    estatus: Mapped[str] = mapped_column(String(20), default="activo")

    first_name: Mapped[str | None] = mapped_column(String(100))
    paternal_last_name: Mapped[str | None] = mapped_column(String(100))
    maternal_last_name: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str | None] = mapped_column(String(255))

    address: Mapped[str | None] = mapped_column(Text)
    colony: Mapped[str | None] = mapped_column(String(150))
    municipality_state: Mapped[str | None] = mapped_column(String(150))
    phone: Mapped[str | None] = mapped_column(String(30))

    emergency_contact_raw: Mapped[str | None] = mapped_column(Text)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(150))
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(30))

    high_school_type: Mapped[str | None] = mapped_column(String(20))
    exam_attempts: Mapped[str | None] = mapped_column(String(30))
    desired_degree: Mapped[str | None] = mapped_column(String(150))
    study_area: Mapped[str | None] = mapped_column(String(80))
    diagnostic_exam: Mapped[bool | None] = mapped_column(Boolean)
    donation_willingness: Mapped[str | None] = mapped_column(String(20))
    presencial_consent: Mapped[bool | None] = mapped_column(Boolean)
    credential_collected: Mapped[bool | None] = mapped_column(Boolean)

    preferred_course_location: Mapped[str | None] = mapped_column(String(150))
    photo_url: Mapped[str | None] = mapped_column(String(500))

    folio: Mapped[int | None] = mapped_column(Integer, unique=True)
    matricula: Mapped[str | None] = mapped_column(String(12), unique=True)
    form_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id", ondelete="CASCADE"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="confirmada")
    payment_status: Mapped[str] = mapped_column(String(20), default="no_requerido")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
