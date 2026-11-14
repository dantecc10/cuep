"""add registration core

Revision ID: b1c2d3e4f5a6
Revises: 9a2b3c4d5e6f
Create Date: 2026-11-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "9a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _try_enable_trgm() -> bool:
    conn = op.get_bind()
    conn.execute(sa.text("SAVEPOINT trgm_ext"))
    try:
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    except Exception:
        conn.execute(sa.text("ROLLBACK TO SAVEPOINT trgm_ext"))
        conn.execute(sa.text("RELEASE SAVEPOINT trgm_ext"))
        return False
    conn.execute(sa.text("RELEASE SAVEPOINT trgm_ext"))
    return True


def _assert_no_duplicates() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM students
                WHERE email IS NOT NULL AND deleted_at IS NULL
                GROUP BY lower(email)
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Hay correos duplicados (case-insensitive) en students; resuélvelos antes de migrar.';
            END IF;
            IF EXISTS (
                SELECT 1 FROM students
                WHERE phone_normalized IS NOT NULL AND deleted_at IS NULL
                GROUP BY phone_normalized
                HAVING count(*) > 1
            ) THEN
                RAISE EXCEPTION 'Hay teléfonos normalizados duplicados en students; resuélvelos antes de migrar.';
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    has_trgm = _try_enable_trgm()

    op.execute("CREATE SEQUENCE IF NOT EXISTS student_folio_seq")
    op.execute(
        "SELECT setval('student_folio_seq', "
        "GREATEST(COALESCE((SELECT MAX(folio) FROM students), 0) + 1, 1), false)"
    )

    op.add_column("students", sa.Column("anio", sa.Integer(), nullable=True))
    op.add_column("students", sa.Column("phone_normalized", sa.String(length=15), nullable=True))
    op.add_column("students", sa.Column("qr_token", sa.String(length=64), nullable=True))
    op.add_column("students", sa.Column("checkin_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("students", sa.Column("checkin_by", sa.Integer(), nullable=True))
    op.add_column("students", sa.Column("checkin_sede_id", sa.Integer(), nullable=True))
    op.add_column(
        "students",
        sa.Column("registration_source", sa.String(length=20), nullable=False, server_default="web"),
    )

    op.execute(
        "UPDATE students SET anio = EXTRACT(YEAR FROM COALESCE(created_at, now()))::int "
        "WHERE anio IS NULL"
    )
    op.execute(
        """
        UPDATE students
        SET phone_normalized = RIGHT(regexp_replace(phone, '[^0-9]', '', 'g'), 10)
        WHERE phone IS NOT NULL
          AND phone_normalized IS NULL
          AND length(regexp_replace(phone, '[^0-9]', '', 'g')) >= 10
        """
    )
    _assert_no_duplicates()

    op.alter_column(
        "students",
        "anio",
        existing_type=sa.Integer(),
        nullable=False,
        server_default=sa.text("EXTRACT(YEAR FROM CURRENT_DATE)::int"),
    )
    op.alter_column(
        "students",
        "estatus",
        existing_type=sa.String(length=20),
        existing_nullable=False,
        server_default="registrado",
    )

    op.create_check_constraint(
        "ck_students_estatus",
        "students",
        "estatus IN ('registrado','en_inscripcion','inscrito','activo','no_asistio','cancelado','baja')",
    )
    op.create_check_constraint(
        "ck_students_registration_source",
        "students",
        "registration_source IN ('web','presencial','importacion','seed')",
    )
    op.create_foreign_key(
        "fk_students_checkin_by_users",
        "students",
        "users",
        ["checkin_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_students_checkin_sede_id_sedes",
        "students",
        "sedes",
        ["checkin_sede_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index("ix_students_anio_estatus", "students", ["anio", "estatus"])
    op.create_index("ix_students_sede_estatus", "students", ["sede_id", "estatus"])
    op.create_index("ix_students_area", "students", ["area"])
    op.create_index("ix_students_created_at", "students", ["created_at"])
    op.create_index("uq_students_qr_token", "students", ["qr_token"], unique=True)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_students_email_lower "
        "ON students (lower(email)) "
        "WHERE email IS NOT NULL AND deleted_at IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_students_phone_normalized "
        "ON students (phone_normalized) "
        "WHERE phone_normalized IS NOT NULL AND deleted_at IS NULL"
    )

    if has_trgm:
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_students_full_name_trgm "
            "ON students USING gin (full_name gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_students_matricula_trgm "
            "ON students USING gin (matricula gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_students_email_trgm "
            "ON students USING gin (email gin_trgm_ops)"
        )

    op.create_table(
        "configuracion_inscripcion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "anio",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("EXTRACT(YEAR FROM CURRENT_DATE)::int"),
        ),
        sa.Column("registro_abierto", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("simulacro_activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "simulacro_monto",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default=sa.text("150.00"),
        ),
        sa.Column("simulacro_moneda", sa.String(length=10), nullable=False, server_default="MXN"),
        sa.Column(
            "pago_efectivo_habilitado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "transferencia_habilitada",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("transferencia_banco", sa.String(length=100), nullable=True),
        sa.Column("transferencia_titular", sa.String(length=150), nullable=True),
        sa.Column("transferencia_clabe", sa.String(length=20), nullable=True),
        sa.Column("transferencia_instrucciones", sa.Text(), nullable=True),
        sa.Column(
            "parcialidades_permitidas",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("parcialidades_max", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "donativo_obligatorio",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("donativo_descripcion", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
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
        sa.CheckConstraint("id = 1", name="ck_configuracion_inscripcion_singleton"),
        sa.CheckConstraint(
            "anio BETWEEN 2000 AND 2100", name="ck_configuracion_inscripcion_anio"
        ),
        sa.CheckConstraint(
            "simulacro_monto >= 0", name="ck_configuracion_inscripcion_simulacro_monto"
        ),
        sa.CheckConstraint(
            "parcialidades_max >= 1", name="ck_configuracion_inscripcion_parcialidades"
        ),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO configuracion_inscripcion (
            id, anio, registro_abierto, simulacro_activo, simulacro_monto,
            simulacro_moneda, pago_efectivo_habilitado, transferencia_habilitada,
            parcialidades_permitidas, parcialidades_max, donativo_obligatorio
        ) VALUES (
            1, EXTRACT(YEAR FROM CURRENT_DATE)::int, true, true, 150.00,
            'MXN', true, false, false, 1, false
        )
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.create_table(
        "eventos_inscripcion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("estado_anterior", sa.String(length=20), nullable=True),
        sa.Column("estado_nuevo", sa.String(length=20), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("sede_id", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tipo IN ('registro','checkin','cambio_estatus','pago_efectivo','pago_comprobante',"
            "'pago_validado','pago_rechazado','pase_generado','notificacion','importacion')",
            name="ck_eventos_inscripcion_tipo",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sede_id"], ["sedes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_eventos_inscripcion_student_created",
        "eventos_inscripcion",
        ["student_id", "created_at"],
    )
    op.create_index(
        "ix_eventos_inscripcion_tipo_created",
        "eventos_inscripcion",
        ["tipo", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_eventos_inscripcion_tipo_created", table_name="eventos_inscripcion")
    op.drop_index("ix_eventos_inscripcion_student_created", table_name="eventos_inscripcion")
    op.drop_table("eventos_inscripcion")
    op.drop_table("configuracion_inscripcion")

    op.execute("DROP INDEX IF EXISTS ix_students_email_trgm")
    op.execute("DROP INDEX IF EXISTS ix_students_matricula_trgm")
    op.execute("DROP INDEX IF EXISTS ix_students_full_name_trgm")
    op.execute("DROP INDEX IF EXISTS uq_students_phone_normalized")
    op.execute("DROP INDEX IF EXISTS uq_students_email_lower")

    op.drop_index("uq_students_qr_token", table_name="students")
    op.drop_index("ix_students_created_at", table_name="students")
    op.drop_index("ix_students_area", table_name="students")
    op.drop_index("ix_students_sede_estatus", table_name="students")
    op.drop_index("ix_students_anio_estatus", table_name="students")

    op.drop_constraint("ck_students_registration_source", "students", type_="check")
    op.drop_constraint("ck_students_estatus", "students", type_="check")
    op.drop_constraint("fk_students_checkin_sede_id_sedes", "students", type_="foreignkey")
    op.drop_constraint("fk_students_checkin_by_users", "students", type_="foreignkey")

    op.alter_column(
        "students",
        "estatus",
        existing_type=sa.String(length=20),
        existing_nullable=False,
        server_default="activo",
    )
    op.drop_column("students", "registration_source")
    op.drop_column("students", "checkin_sede_id")
    op.drop_column("students", "checkin_by")
    op.drop_column("students", "checkin_at")
    op.drop_column("students", "qr_token")
    op.drop_column("students", "phone_normalized")
    op.drop_column("students", "anio")
    op.execute("DROP SEQUENCE IF EXISTS student_folio_seq")
