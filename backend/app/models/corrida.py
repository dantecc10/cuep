from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class CorridaHorario(Base):
    __tablename__ = "corridas_horarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sede_id: Mapped[int | None] = mapped_column(ForeignKey("sedes.id", ondelete="SET NULL"))
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    solicitado_por: Mapped[str | None] = mapped_column(String(100))
    parametros_resumen: Mapped[dict | None] = mapped_column(JSONB)
    resultado_json: Mapped[dict | None] = mapped_column(JSONB)
    metricas_optimizacion: Mapped[dict | None] = mapped_column(JSONB)
    intentos: Mapped[int] = mapped_column(Integer, default=0)
    aprobada: Mapped[bool] = mapped_column(Boolean, default=False)
    aprobada_por: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    aprobada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_inicio: Mapped[date | None] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    publicada: Mapped[bool] = mapped_column(Boolean, default=False)
    publicada_por: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    publicada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    progreso: Mapped[int] = mapped_column(Integer, default=0)
    etapa: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
