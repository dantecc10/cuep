from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
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
    estatus: Mapped[str] = mapped_column(
        String(20), default="registrado", server_default="registrado"
    )
    anio: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("EXTRACT(YEAR FROM CURRENT_DATE)::int")
    )
    phone_normalized: Mapped[str | None] = mapped_column(String(15))
    qr_token: Mapped[str | None] = mapped_column(String(64))
    checkin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    checkin_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    checkin_sede_id: Mapped[int | None] = mapped_column(ForeignKey("sedes.id", ondelete="SET NULL"))
    registration_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="web", server_default="web"
    )

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
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "estatus IN ('registrado','en_inscripcion','inscrito','activo','no_asistio','cancelado','baja')",
            name="ck_students_estatus",
        ),
        CheckConstraint(
            "registration_source IN ('web','presencial','importacion','seed')",
            name="ck_students_registration_source",
        ),
        Index("ix_students_anio_estatus", "anio", "estatus"),
        Index("ix_students_sede_estatus", "sede_id", "estatus"),
        Index("ix_students_area", "area"),
        Index("ix_students_created_at", "created_at"),
        Index("uq_students_qr_token", "qr_token", unique=True),
        Index(
            "uq_students_email_lower",
            func.lower(email),
            unique=True,
            postgresql_where=text("email IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index(
            "uq_students_phone_normalized",
            "phone_normalized",
            unique=True,
            postgresql_where=text("phone_normalized IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index(
            "ix_students_full_name_trgm",
            "full_name",
            postgresql_using="gin",
            postgresql_ops={"full_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_students_matricula_trgm",
            "matricula",
            postgresql_using="gin",
            postgresql_ops={"matricula": "gin_trgm_ops"},
        ),
        Index(
            "ix_students_email_trgm",
            "email",
            postgresql_using="gin",
            postgresql_ops={"email": "gin_trgm_ops"},
        ),
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id", ondelete="CASCADE"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="confirmada")
    payment_status: Mapped[str] = mapped_column(String(20), default="no_requerido")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
