from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

CONCEPTOS_CARGO = ("simulacro", "donativo", "otro")
ESTADOS_CARGO = ("pendiente", "parcial", "pagado", "cancelado", "exento")
METODOS_PAGO = ("efectivo", "transferencia")
ESTADOS_PAGO = ("pendiente", "validado", "rechazado", "cancelado")


class Cargo(Base):
    __tablename__ = "cargos"
    __table_args__ = (
        CheckConstraint("monto >= 0", name="ck_cargos_monto"),
        CheckConstraint(
            "concepto IN ('simulacro','donativo','otro')", name="ck_cargos_concepto"
        ),
        CheckConstraint(
            "estado IN ('pendiente','parcial','pagado','cancelado','exento')",
            name="ck_cargos_estado",
        ),
        Index(
            "uq_cargos_student_anio_concepto",
            "student_id",
            "anio",
            "concepto",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_cargos_student_estado", "student_id", "estado"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    concepto: Mapped[str] = mapped_column(String(30), nullable=False, default="simulacro")
    descripcion: Mapped[str | None] = mapped_column(String(255))
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="MXN")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    fecha_limite: Mapped[date | None] = mapped_column(Date)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Pago(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        CheckConstraint("monto > 0", name="ck_pagos_monto"),
        CheckConstraint(
            "metodo IN ('efectivo','transferencia')", name="ck_pagos_metodo"
        ),
        CheckConstraint(
            "estado IN ('pendiente','validado','rechazado','cancelado')",
            name="ck_pagos_estado",
        ),
        Index(
            "uq_pagos_recibo_codigo",
            "recibo_codigo",
            unique=True,
            postgresql_where=text("recibo_codigo IS NOT NULL"),
        ),
        Index("ix_pagos_cargo_estado", "cargo_id", "estado"),
        Index("ix_pagos_student_created", "student_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cargo_id: Mapped[int] = mapped_column(
        ForeignKey("cargos.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(10), nullable=False, default="MXN")
    metodo: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    referencia: Mapped[str | None] = mapped_column(String(120))
    comprobante_key: Mapped[str | None] = mapped_column(String(500))
    comprobante_nombre: Mapped[str | None] = mapped_column(String(255))
    comprobante_content_type: Mapped[str | None] = mapped_column(String(100))
    comprobante_size: Mapped[int | None] = mapped_column(Integer)
    comprobante_subido_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_pago: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    validado_por: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    validado_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_rechazo: Mapped[str | None] = mapped_column(Text)
    recibo_codigo: Mapped[str | None] = mapped_column(String(24))
    recibo_emitido_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
