from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id", ondelete="CASCADE"), nullable=False)
    nivel: Mapped[str] = mapped_column(String(20), nullable=False)
    area: Mapped[str | None] = mapped_column(String(50))
    estatus: Mapped[str] = mapped_column(String(20), default="activo")
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
