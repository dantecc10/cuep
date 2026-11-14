"""seed notification templates

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-11-14 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e4f5a6b7c8d9"
down_revision: Union[str, None] = "d3e4f5a6b7c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TEMPLATES = (
    (
        "registro_confirmado",
        "Registro confirmado",
        "Tu registro al CUEP quedó confirmado",
        "Hola $nombre:\n\nTu registro al CUEP quedó confirmado.\n\nMatrícula: $matricula\nSede: $sede\n\nConserva tu matrícula y presenta tu pase digital cuando acudas a la inscripción presencial.\n\nColectivo Universitario por la Educación Popular",
        '["nombre","matricula","sede"]',
    ),
    (
        "pase_inscripcion",
        "Pase de inscripción",
        "Tu pase para la inscripción presencial",
        "Hola $nombre:\n\nEste es tu pase para la inscripción presencial.\n\nMatrícula: $matricula\nSede: $sede\n\nPresenta el código QR adjunto. Tu pago del simulacro no es obligatorio para inscribirte.\n\nCUEP",
        '["nombre","matricula","sede"]',
    ),
    (
        "recordatorio_inscripcion_presencial",
        "Recordatorio de inscripción",
        "Recuerda tu inscripción presencial",
        "Hola $nombre:\n\nTe recordamos acudir a la inscripción presencial en $sede. Lleva tu pase digital y una identificación.\n\nMatrícula: $matricula\n\nCUEP",
        '["nombre","matricula","sede"]',
    ),
    (
        "checkin_confirmado",
        "Check-in confirmado",
        "Tu check-in quedó registrado",
        "Hola $nombre:\n\nTu check-in en $sede quedó registrado correctamente.\n\nMatrícula: $matricula\n\nCUEP",
        '["nombre","matricula","sede"]',
    ),
    (
        "simulacro_confirmado",
        "Simulacro confirmado",
        "Tu lugar para el simulacro quedó registrado",
        "Hola $nombre:\n\nRegistramos tu interés en el simulacro.\n\nMonto: $monto $moneda\nMatrícula: $matricula\n\nPuedes pagar en efectivo durante la inscripción presencial o subir tu comprobante de transferencia.\n\nCUEP",
        '["nombre","matricula","monto","moneda"]',
    ),
    (
        "pago_recibido",
        "Pago recibido",
        "Recibimos tu comprobante de pago",
        "Hola $nombre:\n\nRecibimos tu comprobante de pago por $monto $moneda. El equipo lo revisará y te avisaremos cuando quede validado.\n\nMatrícula: $matricula\n\nCUEP",
        '["nombre","matricula","monto","moneda"]',
    ),
    (
        "pago_validado",
        "Pago validado",
        "Tu pago quedó validado",
        "Hola $nombre:\n\nTu pago por $monto $moneda quedó validado.\n\nRecibo: $recibo\nMatrícula: $matricula\n\nPuedes descargar tu recibo desde el portal.\n\nCUEP",
        '["nombre","matricula","monto","moneda","recibo"]',
    ),
    (
        "pago_rechazado",
        "Pago rechazado",
        "Tu comprobante de pago fue rechazado",
        "Hola $nombre:\n\nNo pudimos validar tu comprobante de pago.\n\nMotivo: $motivo\nMatrícula: $matricula\n\nPuedes subir un nuevo comprobante o pagar en efectivo durante la inscripción presencial.\n\nCUEP",
        '["nombre","matricula","motivo"]',
    ),
    (
        "credencial_lista",
        "Credencial lista",
        "Tu credencial del CUEP está lista",
        "Hola $nombre:\n\nTu credencial del CUEP está lista para recoger en $sede.\n\nMatrícula: $matricula\n\nCUEP",
        '["nombre","matricula","sede"]',
    ),
)


def upgrade() -> None:
    for clave, nombre, asunto, cuerpo, variables in TEMPLATES:
        op.execute(
            f"""
            INSERT INTO notificacion_plantillas (clave, nombre, asunto, cuerpo_texto, variables, activo)
            VALUES (
                '{clave}',
                '{nombre}',
                '{asunto}',
                '{cuerpo.replace("'", "''")}',
                '{variables}'::jsonb,
                true
            )
            ON CONFLICT (clave) DO NOTHING
            """
        )


def downgrade() -> None:
    claves = ", ".join(f"'{item[0]}'" for item in TEMPLATES)
    op.execute(f"DELETE FROM notificacion_plantillas WHERE clave IN ({claves})")
