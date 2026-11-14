"""allow simulated notifications in the outbox

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-11-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f5a6b7c8d9e0"
down_revision: Union[str, None] = "e4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ESTADO_CHECK = (
    "estado IN ('pendiente','enviado','simulado','error','cancelado')"
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_notificacion_outbox_estado",
        "notificacion_outbox",
        type_="check",
    )
    op.create_check_constraint(
        "ck_notificacion_outbox_estado",
        "notificacion_outbox",
        ESTADO_CHECK,
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_notificacion_outbox_estado",
        "notificacion_outbox",
        type_="check",
    )
    op.create_check_constraint(
        "ck_notificacion_outbox_estado",
        "notificacion_outbox",
        "estado IN ('pendiente','enviado','error','cancelado')",
    )
