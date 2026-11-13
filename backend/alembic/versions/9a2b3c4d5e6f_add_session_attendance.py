"""add session attendance

Revision ID: 9a2b3c4d5e6f
Revises: 8f1c2d3e4a5b
Create Date: 2026-11-13 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9a2b3c4d5e6f'
down_revision: Union[str, None] = '8f1c2d3e4a5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('corridas_horarios', sa.Column('fecha_inicio', sa.Date(), nullable=True))
    op.add_column('corridas_horarios', sa.Column('fecha_fin', sa.Date(), nullable=True))

    op.create_table(
        'sesiones_clase',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('corrida_id', sa.Integer(), nullable=True),
        sa.Column('sede_id', sa.Integer(), nullable=False),
        sa.Column('grupo_id', sa.Integer(), nullable=False),
        sa.Column('tutor_id', sa.Integer(), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('dia_semana', sa.Integer(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column('hora_fin', sa.Time(), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False, server_default='pendiente'),
        sa.Column('tutor_cubridor_id', sa.Integer(), nullable=True),
        sa.Column('comentario', sa.Text(), nullable=True),
        sa.Column('origen', sa.String(length=20), nullable=False, server_default='automatica'),
        sa.Column('registrado_por', sa.Integer(), nullable=True),
        sa.Column('actualizado_por', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "estado IN ('pendiente','asistio','retardo','falta','justificada','cancelada','cubierta')",
            name='ck_sesion_clase_estado',
        ),
        sa.CheckConstraint("origen IN ('automatica','manual')", name='ck_sesion_clase_origen'),
        sa.ForeignKeyConstraint(['actualizado_por'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['corrida_id'], ['corridas_horarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['grupo_id'], ['grupos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['registrado_por'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sede_id'], ['sedes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tutor_cubridor_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tutor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grupo_id', 'tutor_id', 'fecha', 'hora_inicio', name='uq_sesion_clase_horario'),
    )
    op.create_index('ix_sesiones_clase_sede_fecha', 'sesiones_clase', ['sede_id', 'fecha'])
    op.create_index('ix_sesiones_clase_tutor_fecha', 'sesiones_clase', ['tutor_id', 'fecha'])
    op.create_index('ix_sesiones_clase_cubridor_fecha', 'sesiones_clase', ['tutor_cubridor_id', 'fecha'])
    op.create_index('ix_sesiones_clase_estado_fecha', 'sesiones_clase', ['estado', 'fecha'])


def downgrade() -> None:
    op.drop_index('ix_sesiones_clase_estado_fecha', table_name='sesiones_clase')
    op.drop_index('ix_sesiones_clase_cubridor_fecha', table_name='sesiones_clase')
    op.drop_index('ix_sesiones_clase_tutor_fecha', table_name='sesiones_clase')
    op.drop_index('ix_sesiones_clase_sede_fecha', table_name='sesiones_clase')
    op.drop_table('sesiones_clase')
    op.drop_column('corridas_horarios', 'fecha_fin')
    op.drop_column('corridas_horarios', 'fecha_inicio')
