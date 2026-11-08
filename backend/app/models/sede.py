from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Sede(Base):
    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Grupo(Base):
    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id", ondelete="CASCADE"), nullable=False)
    materia_id: Mapped[int] = mapped_column(ForeignKey("materias.id", ondelete="CASCADE"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    horas_totales: Mapped[int] = mapped_column(Integer, nullable=False)
    bloque_horas: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    capacidad: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
