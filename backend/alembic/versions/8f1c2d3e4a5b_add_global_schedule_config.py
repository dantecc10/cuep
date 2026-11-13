"""add global schedule config

Revision ID: 8f1c2d3e4a5b
Revises: b7e4c1a92f30
Create Date: 2026-11-13 00:00:00.000000

"""
from datetime import time
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8f1c2d3e4a5b'
down_revision: Union[str, None] = 'b7e4c1a92f30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    config_table = op.create_table(
        'configuracion_horario_dias',
        sa.Column('dia_semana', sa.Integer(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('hora_inicio', sa.Time(), nullable=False, server_default='08:00:00'),
        sa.Column('hora_fin', sa.Time(), nullable=False, server_default='20:00:00'),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('dia_semana'),
    )
    op.bulk_insert(
        config_table,
        [
            {'dia_semana': 1, 'activo': False, 'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
            {'dia_semana': 2, 'activo': False, 'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
            {'dia_semana': 3, 'activo': False, 'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
            {'dia_semana': 4, 'activo': False, 'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
            {'dia_semana': 5, 'activo': False, 'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
            {'dia_semana': 6, 'activo': True, 'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
            {'dia_semana': 7, 'activo': True, 'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
        ],
    )


def downgrade() -> None:
    op.drop_table('configuracion_horario_dias')
