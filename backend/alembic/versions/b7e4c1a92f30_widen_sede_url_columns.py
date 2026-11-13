"""widen sede url columns

Revision ID: b7e4c1a92f30
Revises: cf22a955b8e6
Create Date: 2026-11-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e4c1a92f30'
down_revision: Union[str, None] = 'cf22a955b8e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'sedes',
        'image_url',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        'sedes',
        'maps_url',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'sedes',
        'maps_url',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        'sedes',
        'image_url',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
