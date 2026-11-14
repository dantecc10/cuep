from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ESTADOS_INSCRIPCION = (
    "registrado",
    "en_inscripcion",
    "inscrito",
    "activo",
    "no_asistio",
    "cancelado",
    "baja",
)
ORIGENES_REGISTRO = ("web", "presencial", "importacion", "seed")
TIPOS_EVENTO_INSCRIPCION = (
    "registro",
    "checkin",
    "cambio_estatus",
    "pago_efectivo",
    "pago_comprobante",
    "pago_validado",
    "pago_rechazado",
    "pase_generado",
    "notificacion",
    "importacion",
)


class ConfiguracionInscripcion(Base):
    __tablename__ = "configuracion_inscripcion"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_configuracion_inscripcion_singleton"),
        CheckConstraint("anio BETWEEN 2000 AND 2100", name="ck_configuracion_inscripcion_anio"),
        CheckConstraint("simulacro_monto >= 0", name="ck_configuracion_inscripcion_simulacro_monto"),
        CheckConstraint("parcialidades_max >= 1", name="ck_configuracion_inscripcion_parcialidades"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    anio: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("EXTRACT(YEAR FROM CURRENT_DATE)::int"),
    )
    registro_abierto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    simulacro_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    simulacro_monto: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("150.00")
    )
    simulacro_moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="MXN")
    pago_efectivo_habilitado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    transferencia_habilitada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transferencia_banco: Mapped[str | None] = mapped_column(String(100))
    transferencia_titular: Mapped[str | None] = mapped_column(String(150))
    transferencia_clabe: Mapped[str | None] = mapped_column(String(20))
    transferencia_instrucciones: Mapped[str | None] = mapped_column(Text)
    parcialidades_permitidas: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parcialidades_max: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    donativo_obligatorio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    donativo_descripcion: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EventoInscripcion(Base):
    __tablename__ = "eventos_inscripcion"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('registro','checkin','cambio_estatus','pago_efectivo','pago_comprobante',"
            "'pago_validado','pago_rechazado','pase_generado','notificacion','importacion')",
            name="ck_eventos_inscripcion_tipo",
        ),
        Index("ix_eventos_inscripcion_student_created", "student_id", "created_at"),
        Index("ix_eventos_inscripcion_tipo_created", "tipo", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    estado_anterior: Mapped[str | None] = mapped_column(String(20))
    estado_nuevo: Mapped[str | None] = mapped_column(String(20))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    sede_id: Mapped[int | None] = mapped_column(ForeignKey("sedes.id", ondelete="SET NULL"))
    detalle: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
