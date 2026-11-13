from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ESTADOS_ASISTENCIA = (
    "pendiente",
    "asistio",
    "retardo",
    "falta",
    "justificada",
    "cancelada",
    "cubierta",
)
ORIGENES_SESION = ("automatica", "manual")


class SesionClase(Base):
    __tablename__ = "sesiones_clase"
    __table_args__ = (
        UniqueConstraint("grupo_id", "tutor_id", "fecha", "hora_inicio", name="uq_sesion_clase_horario"),
        CheckConstraint(
            "estado IN ('pendiente','asistio','retardo','falta','justificada','cancelada','cubierta')",
            name="ck_sesion_clase_estado",
        ),
        CheckConstraint("origen IN ('automatica','manual')", name="ck_sesion_clase_origen"),
        Index("ix_sesiones_clase_sede_fecha", "sede_id", "fecha"),
        Index("ix_sesiones_clase_tutor_fecha", "tutor_id", "fecha"),
        Index("ix_sesiones_clase_cubridor_fecha", "tutor_cubridor_id", "fecha"),
        Index("ix_sesiones_clase_estado_fecha", "estado", "fecha"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    corrida_id: Mapped[int | None] = mapped_column(ForeignKey("corridas_horarios.id", ondelete="SET NULL"))
    sede_id: Mapped[int] = mapped_column(ForeignKey("sedes.id", ondelete="CASCADE"), nullable=False)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupos.id", ondelete="CASCADE"), nullable=False)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    tutor_cubridor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    comentario: Mapped[str | None] = mapped_column(Text)
    origen: Mapped[str] = mapped_column(String(20), nullable=False, default="automatica")
    registrado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    actualizado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
