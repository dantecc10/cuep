"""add group assignment events and templates

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-11-15 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TIPO_CHECK = (
    "tipo IN ('registro','checkin','cambio_estatus','pago_efectivo','pago_comprobante',"
    "'pago_validado','pago_rechazado','pase_generado','notificacion','importacion',"
    "'asignacion_grupo')"
)

TEMPLATES = (
    (
        "grupo_asignado",
        "Grupo asignado",
        "Te asignamos un grupo de asesoría",
        "Hola $nombre:\n\nTe asignamos el grupo $grupo de la materia $materia.\n\n"
        "Matrícula: $matricula\nSede: $sede\nEstado: $estado\n\n"
        "CUEP",
        '["nombre","matricula","sede","grupo","materia","estado"]',
    ),
    (
        "estado_inscripcion",
        "Estado de inscripción actualizado",
        "Actualizamos tu inscripción a un grupo",
        "Hola $nombre:\n\nTu inscripción al grupo $grupo ahora está $estado.\n\n"
        "Matrícula: $matricula\nSede: $sede\n\nCUEP",
        '["nombre","matricula","sede","grupo","estado"]',
    ),
    (
        "promocion_lista_espera",
        "Promoción de lista de espera",
        "Avanzaste de la lista de espera",
        "Hola $nombre:\n\nPasaste de la lista de espera al grupo $grupo de la materia $materia.\n\n"
        "Matrícula: $matricula\nSede: $sede\n\nCUEP",
        '["nombre","matricula","sede","grupo","materia"]',
    ),
)


def upgrade() -> None:
    op.drop_constraint(
        "ck_eventos_inscripcion_tipo",
        "eventos_inscripcion",
        type_="check",
    )
    op.create_check_constraint(
        "ck_eventos_inscripcion_tipo",
        "eventos_inscripcion",
        TIPO_CHECK,
    )

    table = sa.table(
        "notificacion_plantillas",
        sa.column("clave", sa.String),
        sa.column("nombre", sa.String),
        sa.column("asunto", sa.String),
        sa.column("cuerpo_texto", sa.Text),
        sa.column("variables", postgresql.JSONB(astext_type=sa.Text())),
        sa.column("activo", sa.Boolean),
    )
    for clave, nombre, asunto, cuerpo, variables in TEMPLATES:
        op.execute(
            postgresql.insert(table)
            .values(
                clave=clave,
                nombre=nombre,
                asunto=asunto,
                cuerpo_texto=cuerpo,
                variables=variables,
                activo=True,
            )
            .on_conflict_do_nothing(index_elements=["clave"])
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM notificacion_plantillas "
        "WHERE clave IN ('grupo_asignado','estado_inscripcion','promocion_lista_espera')"
    )
    op.drop_constraint(
        "ck_eventos_inscripcion_tipo",
        "eventos_inscripcion",
        type_="check",
    )
    op.create_check_constraint(
        "ck_eventos_inscripcion_tipo",
        "eventos_inscripcion",
        "tipo IN ('registro','checkin','cambio_estatus','pago_efectivo','pago_comprobante',"
        "'pago_validado','pago_rechazado','pase_generado','notificacion','importacion')",
    )
