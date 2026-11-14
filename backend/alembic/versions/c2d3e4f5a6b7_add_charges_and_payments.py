"""add charges and payments

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-11-14 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cargos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("concepto", sa.String(length=30), nullable=False, server_default="simulacro"),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("monto", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("moneda", sa.String(length=10), nullable=False, server_default="MXN"),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="pendiente"),
        sa.Column("fecha_limite", sa.Date(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("monto >= 0", name="ck_cargos_monto"),
        sa.CheckConstraint(
            "concepto IN ('simulacro','donativo','otro')", name="ck_cargos_concepto"
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente','parcial','pagado','cancelado','exento')",
            name="ck_cargos_estado",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_cargos_student_anio_concepto",
        "cargos",
        ["student_id", "anio", "concepto"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_cargos_student_estado", "cargos", ["student_id", "estado"])

    op.create_table(
        "pagos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cargo_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("monto", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("moneda", sa.String(length=10), nullable=False, server_default="MXN"),
        sa.Column("metodo", sa.String(length=20), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="pendiente"),
        sa.Column("referencia", sa.String(length=120), nullable=True),
        sa.Column("comprobante_key", sa.String(length=500), nullable=True),
        sa.Column("comprobante_nombre", sa.String(length=255), nullable=True),
        sa.Column("comprobante_content_type", sa.String(length=100), nullable=True),
        sa.Column("comprobante_size", sa.Integer(), nullable=True),
        sa.Column("comprobante_subido_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_pago", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validado_por", sa.Integer(), nullable=True),
        sa.Column("validado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_rechazo", sa.Text(), nullable=True),
        sa.Column("recibo_codigo", sa.String(length=24), nullable=True),
        sa.Column("recibo_emitido_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("monto > 0", name="ck_pagos_monto"),
        sa.CheckConstraint(
            "metodo IN ('efectivo','transferencia')", name="ck_pagos_metodo"
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente','validado','rechazado','cancelado')",
            name="ck_pagos_estado",
        ),
        sa.ForeignKeyConstraint(["cargo_id"], ["cargos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["validado_por"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_pagos_recibo_codigo",
        "pagos",
        ["recibo_codigo"],
        unique=True,
        postgresql_where=sa.text("recibo_codigo IS NOT NULL"),
    )
    op.create_index("ix_pagos_cargo_estado", "pagos", ["cargo_id", "estado"])
    op.create_index("ix_pagos_student_created", "pagos", ["student_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_pagos_student_created", table_name="pagos")
    op.drop_index("ix_pagos_cargo_estado", table_name="pagos")
    op.drop_index("uq_pagos_recibo_codigo", table_name="pagos")
    op.drop_table("pagos")

    op.drop_index("ix_cargos_student_estado", table_name="cargos")
    op.drop_index("uq_cargos_student_anio_concepto", table_name="cargos")
    op.drop_table("cargos")
