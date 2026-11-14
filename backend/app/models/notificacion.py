from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

ESTADOS_OUTBOX = ("pendiente", "enviado", "error", "cancelado")


class NotificacionPlantilla(Base):
    __tablename__ = "notificacion_plantillas"
    __table_args__ = (
        Index("ix_notificacion_plantillas_activo", "activo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo_texto: Mapped[str] = mapped_column(Text, nullable=False)
    cuerpo_html: Mapped[str | None] = mapped_column(Text)
    variables: Mapped[list | None] = mapped_column(JSONB)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NotificacionOutbox(Base):
    __tablename__ = "notificacion_outbox"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente','enviado','error','cancelado')",
            name="ck_notificacion_outbox_estado",
        ),
        CheckConstraint("intentos >= 0", name="ck_notificacion_outbox_intentos"),
        Index(
            "uq_notificacion_outbox_dedupe",
            "dedupe_key",
            unique=True,
            postgresql_where=text("dedupe_key IS NOT NULL"),
        ),
        Index("ix_notificacion_outbox_estado_programado", "estado", "programado_para"),
        Index("ix_notificacion_outbox_student_created", "student_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plantilla_id: Mapped[int | None] = mapped_column(
        ForeignKey("notificacion_plantillas.id", ondelete="SET NULL")
    )
    plantilla_clave: Mapped[str | None] = mapped_column(String(80))
    student_id: Mapped[int | None] = mapped_column(
        ForeignKey("students.id", ondelete="SET NULL")
    )
    destinatario_email: Mapped[str] = mapped_column(String(255), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo_texto: Mapped[str] = mapped_column(Text, nullable=False)
    cuerpo_html: Mapped[str | None] = mapped_column(Text)
    contexto: Mapped[dict | None] = mapped_column(JSONB)
    dedupe_key: Mapped[str | None] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ultimo_error: Mapped[str | None] = mapped_column(Text)
    programado_para: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    enviado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
