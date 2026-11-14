#!/usr/bin/env python3
"""Cierra el ciclo anual de inscripción y abre el siguiente.

El cierre es no destructivo: conserva alumnos, cargos, pagos y eventos del
ciclo anterior. Cambia el año activo en `configuracion_inscripcion` y deja el
registro cerrado para que la administración revise la configuración del nuevo
ciclo antes de abrirlo.

Uso habitual:
    python backend/scripts/reset_academic_year.py --year 2027 \
        --confirm "RESET 2027" --export-csv /backups/inscripciones-2026.csv

Opciones adicionales:
    --close-only       Solo cierra el registro del año vigente.
    --open-registration Deja el nuevo año con registro abierto.
    --backup FILE      Crea un respaldo con pg_dump antes de modificar.
    --purge-demo       Borra aspirantes demo generados por seed_aspirantes_demo.
    --dry-run          Muestra el plan sin escribir.

Confirmación requerida:
    RESET <anio>       Para avanzar de año.
    CLOSE <anio>       Para cerrar el año vigente sin avanzarlo.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from dotenv import load_dotenv
from sqlalchemy import bindparam, func, select, text
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = BACKEND_ROOT / ".env"
RESET_LOCK_KEY = 0x43554552
DEMO_EMAIL_SUFFIX = "@cuep.example.com"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class ResetError(RuntimeError):
    pass


def _database_url() -> str:
    from app.core.config import settings

    url = make_url(settings.DATABASE_URL)
    drivername = "postgresql+psycopg" if "postgresql+psycopg" in url.drivername else "postgresql"
    return url.set(drivername=drivername).render_as_string(hide_password=False)


async def _snapshot(db: Any, year: int) -> dict[str, Any]:
    from app.models.pago import Cargo, Pago
    from app.models.student import Student

    total = await db.execute(select(func.count()).select_from(Student))
    year_total = await db.execute(
        select(func.count()).select_from(Student).where(
            Student.anio == year, Student.deleted_at.is_(None)
        )
    )
    statuses = await db.execute(
        select(Student.estatus, func.count())
        .where(Student.anio == year, Student.deleted_at.is_(None))
        .group_by(Student.estatus)
    )
    cargos = await db.execute(
        select(Cargo.estado, func.count())
        .join(Student, Student.id == Cargo.student_id)
        .where(Student.anio == year, Cargo.deleted_at.is_(None))
        .group_by(Cargo.estado)
    )
    pagos = await db.execute(
        select(Pago.metodo, Pago.estado, func.count())
        .join(Student, Student.id == Pago.student_id)
        .where(Student.anio == year, Pago.deleted_at.is_(None))
        .group_by(Pago.metodo, Pago.estado)
    )
    demo = await db.execute(
        select(func.count()).select_from(Student).where(
            Student.registration_source == "seed",
            Student.email.ilike(f"%{DEMO_EMAIL_SUFFIX}"),
            Student.deleted_at.is_(None),
        )
    )
    return {
        "total_students": int(total.scalar_one()),
        "year_students": int(year_total.scalar_one()),
        "statuses": dict(statuses.all()),
        "cargos": dict(cargos.all()),
        "pagos": {f"{metodo}/{estado}": count for metodo, estado, count in pagos.all()},
        "demo_students": int(demo.scalar_one()),
    }


async def _export_csv(path: Path, db: Any, year: int) -> int:
    from app.models.sede import Sede
    from app.models.student import Student

    students = (
        await db.execute(
            select(Student)
            .where(Student.anio == year, Student.deleted_at.is_(None))
            .order_by(Student.created_at.asc())
        )
    ).scalars().all()
    sede_ids = {student.sede_id for student in students if student.sede_id}
    sedes = {}
    if sede_ids:
        sedes = {
            sede.id: sede.nombre
            for sede in (
                await db.execute(select(Sede).where(Sede.id.in_(sede_ids)))
            ).scalars().all()
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "matricula",
                "folio",
                "nombre",
                "email",
                "telefono",
                "nivel",
                "area",
                "sede",
                "estatus",
                "anio",
                "checkin_at",
                "created_at",
            ]
        )
        for student in students:
            writer.writerow(
                [
                    student.matricula or "",
                    student.folio or "",
                    student.full_name or "",
                    student.email or "",
                    student.phone or "",
                    student.nivel,
                    student.area or "",
                    sedes.get(student.sede_id, ""),
                    student.estatus,
                    student.anio,
                    student.checkin_at.isoformat() if student.checkin_at else "",
                    student.created_at.isoformat() if student.created_at else "",
                ]
            )
    return len(students)


def _run_backup(backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    command = ["pg_dump", "--no-owner", "--no-privileges", "--file", str(backup_path)]
    try:
        subprocess.run(command + [_database_url()], check=True)
    except FileNotFoundError as exc:
        raise ResetError("No se encontró pg_dump para crear el respaldo.") from exc
    except subprocess.CalledProcessError as exc:
        raise ResetError(f"pg_dump falló con código {exc.returncode}.") from exc


async def _purge_demo(db: Any, year: int) -> dict[str, int]:
    from app.models.student import Student

    students = (
        (
            await db.execute(
                select(Student).where(
                    Student.anio == year,
                    Student.registration_source == "seed",
                    Student.email.ilike(f"%{DEMO_EMAIL_SUFFIX}"),
                    Student.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    if not students:
        return {"students": 0, "users": 0, "relations": 0}

    student_ids = [student.id for student in students]
    user_ids = [student.user_id for student in students if student.user_id is not None]
    ids_param = bindparam("ids", expanding=True)

    relation_tables = (
        "pagos",
        "cargos",
        "notificacion_outbox",
        "eventos_inscripcion",
        "enrollments",
    )
    relations = 0
    for table in relation_tables:
        result = await db.execute(
            text(f"DELETE FROM {table} WHERE student_id IN :ids").bindparams(ids_param),
            {"ids": student_ids},
        )
        relations += int(result.rowcount or 0)

    await db.execute(
        text("DELETE FROM students WHERE id IN :ids").bindparams(ids_param),
        {"ids": student_ids},
    )
    users = 0
    if user_ids:
        result = await db.execute(
            text("DELETE FROM users WHERE id IN :ids").bindparams(ids_param),
            {"ids": user_ids},
        )
        users = int(result.rowcount or 0)
    return {"students": len(student_ids), "users": users, "relations": relations}


async def reset_academic_year(
    db: Any,
    *,
    target_year: int | None,
    close_only: bool,
    open_registration: bool,
    export_csv: Path | None,
    purge_demo: bool,
    dry_run: bool,
) -> dict[str, Any]:
    from app.services.inscripcion import get_config

    config = await get_config(db, for_update=True)
    current_year = config.anio
    new_year = target_year if not close_only else current_year
    if new_year is None:
        new_year = datetime.now(timezone.utc).year + 1
    if not close_only and new_year <= current_year:
        raise ResetError(
            f"El nuevo año debe ser mayor al año vigente ({current_year})."
        )

    snapshot = await _snapshot(db, current_year)
    exported = 0
    if export_csv is not None and not dry_run:
        exported = await _export_csv(export_csv, db, current_year)

    if close_only:
        config.registro_abierto = False
    else:
        config.anio = new_year
        config.registro_abierto = open_registration

    purged = {"students": 0, "users": 0, "relations": 0}
    if purge_demo:
        purged = await _purge_demo(db, current_year)

    result = {
        "previous_year": current_year,
        "new_year": new_year,
        "close_only": close_only,
        "registration_open": config.registro_abierto,
        "snapshot": snapshot,
        "exported_csv_rows": exported,
        "purged_demo": purged,
        "dry_run": dry_run,
    }

    if dry_run:
        await db.rollback()
    else:
        await db.flush()
    return result


def _confirm_required(args: argparse.Namespace, current_year: int, target_year: int) -> str:
    if args.dry_run:
        return ""
    phrase = args.confirm.strip() if args.confirm else ""
    verb = "CLOSE" if args.close_only else "RESET"
    year = current_year if args.close_only else target_year
    expected = f"{verb} {year}"
    if phrase != expected:
        raise ResetError(f"Confirmación inválida. Escribe exactamente: {expected}")
    return phrase


async def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Cierra el ciclo anual de inscripción y prepara el siguiente."
    )
    parser.add_argument("--year", type=int, help="Año del nuevo ciclo (por defecto: vigente + 1)")
    parser.add_argument(
        "--close-only",
        action="store_true",
        help="Solo cierra el registro del año vigente; no avanza de año.",
    )
    parser.add_argument(
        "--open-registration",
        action="store_true",
        help="Deja el nuevo ciclo con registro abierto (por defecto queda cerrado).",
    )
    parser.add_argument("--export-csv", type=Path, help="Ruta del CSV con el padrón del ciclo saliente")
    parser.add_argument("--backup", type=Path, help="Ruta del respaldo pg_dump previo")
    parser.add_argument(
        "--purge-demo",
        action="store_true",
        help="Borra aspirantes demo del ciclo saliente junto con sus registros relacionados.",
    )
    parser.add_argument("--confirm", help="Frase de confirmación; requerida para escribir.")
    parser.add_argument("--dry-run", action="store_true", help="No escribe cambios.")
    args = parser.parse_args(argv)

    load_dotenv(DEFAULT_ENV_FILE)
    from app.core.database import async_session_factory

    if args.close_only and args.year is not None:
        raise SystemExit("--close-only no usa --year.")
    if args.backup is not None and args.dry_run:
        raise SystemExit("--backup no puede usarse con --dry-run.")

    async with async_session_factory() as db:
        try:
            await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": RESET_LOCK_KEY})
            from app.services.inscripcion import get_config

            config = await get_config(db)
            target_year = config.anio if args.close_only else (args.year or config.anio + 1)
            _confirm_required(args, config.anio, target_year)
            if args.backup is not None:
                _run_backup(args.backup)
            result = await reset_academic_year(
                db,
                target_year=target_year,
                close_only=args.close_only,
                open_registration=args.open_registration,
                export_csv=args.export_csv,
                purge_demo=args.purge_demo,
                dry_run=args.dry_run,
            )
            if not args.dry_run:
                await db.commit()
        except Exception:
            await db.rollback()
            raise

    print(
        f"Cierre anual {'(dry-run)' if args.dry_run else ''}: "
        f"{result['previous_year']} -> {result['new_year']}"
    )
    print(f"Registro: {'abierto' if result['registration_open'] else 'cerrado'}")
    print(
        "Padrón saliente: "
        f"{result['snapshot']['year_students']} estudiantes, "
        f"{len(result['snapshot']['statuses'])} estatus"
    )
    if result["exported_csv_rows"]:
        print(f"CSV exportado: {args.export_csv} ({result['exported_csv_rows']} filas)")
    if args.backup is not None:
        print(f"Respaldo: {args.backup}")
    if args.purge_demo:
        purged = result["purged_demo"]
        print(
            "Demo purgado: "
            f"{purged['students']} estudiantes, {purged['users']} usuarios, "
            f"{purged['relations']} registros relacionados"
        )
    print(
        "Nota: el ciclo anterior sigue disponible consultando la API con "
        "el parámetro anio del año saliente."
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ResetError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
