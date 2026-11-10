from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Sede(Base):
    __tablename__ = "sedes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    ciudad: Mapped[str | None] = mapped_column(String(100))
    codigo: Mapped[str | None] = mapped_column(String(1), unique=True)
    waitlist_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_amount: Mapped[float] = mapped_column(Float, default=0)
    payment_currency: Mapped[str] = mapped_column(String(10), default="MXN")
    descripcion: Mapped[str | None] = mapped_column(Text)
    maps_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
    capacidad: Mapped[int] = mapped_column(Integer, default=30)
    min_alumnos: Mapped[int] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
