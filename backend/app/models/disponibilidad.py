from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Time, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DisponibilidadTutor(Base):
    __tablename__ = "disponibilidad_tutor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_inicio: Mapped[datetime] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[datetime] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TutorMateria(Base):
    __tablename__ = "tutor_materias"

    tutor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    materia_id: Mapped[int] = mapped_column(ForeignKey("materias.id", ondelete="CASCADE"), primary_key=True)
    nivel_preferencia: Mapped[int] = mapped_column(Integer, default=1)
    vetada: Mapped[bool] = mapped_column(Boolean, default=False)
