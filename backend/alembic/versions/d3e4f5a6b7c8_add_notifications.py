"""add notifications

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-11-14 00:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notificacion_plantillas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clave", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("asunto", sa.String(length=255), nullable=False),
        sa.Column("cuerpo_texto", sa.Text(), nullable=False),
        sa.Column("cuerpo_html", sa.Text(), nullable=True),
        sa.Column("variables", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clave"),
    )
    op.create_index("ix_notificacion_plantillas_activo", "notificacion_plantillas", ["activo"])

    op.create_table(
        "notificacion_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plantilla_id", sa.Integer(), nullable=True),
        sa.Column("plantilla_clave", sa.String(length=80), nullable=True),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("destinatario_email", sa.String(length=255), nullable=False),
        sa.Column("asunto", sa.String(length=255), nullable=False),
        sa.Column("cuerpo_texto", sa.Text(), nullable=False),
        sa.Column("cuerpo_html", sa.Text(), nullable=True),
        sa.Column("contexto", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="pendiente"),
        sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ultimo_error", sa.Text(), nullable=True),
        sa.Column(
            "programado_para",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "estado IN ('pendiente','enviado','error','cancelado')",
            name="ck_notificacion_outbox_estado",
        ),
        sa.CheckConstraint("intentos >= 0", name="ck_notificacion_outbox_intentos"),
        sa.ForeignKeyConstraint(["plantilla_id"], ["notificacion_plantillas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_notificacion_outbox_dedupe",
        "notificacion_outbox",
        ["dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )
    op.create_index(
        "ix_notificacion_outbox_estado_programado",
        "notificacion_outbox",
        ["estado", "programado_para"],
    )
    op.create_index(
        "ix_notificacion_outbox_student_created",
        "notificacion_outbox",
        ["student_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notificacion_outbox_student_created", table_name="notificacion_outbox"
    )
    op.drop_index(
        "ix_notificacion_outbox_estado_programado", table_name="notificacion_outbox"
    )
    op.drop_index("uq_notificacion_outbox_dedupe", table_name="notificacion_outbox")
    op.drop_table("notificacion_outbox")

    op.drop_index("ix_notificacion_plantillas_activo", table_name="notificacion_plantillas")
    op.drop_table("notificacion_plantillas")
