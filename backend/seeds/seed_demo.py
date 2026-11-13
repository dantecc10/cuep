from __future__ import annotations

# ruff: noqa: E402

import argparse
import asyncio
import getpass
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.models.disponibilidad import DisponibilidadTutor, TutorMateria
from app.models.materia import Materia
from app.models.plan import PlanEstudio, plan_materias
from app.models.sede import Grupo, Sede
from app.models.user import User
from app.services.horario import cargar_horario
from seeds.demo_catalog import (
    MATERIA_BY_KEY,
    EMAIL_DOMAIN,
    PASSWORD_ENV,
    PLAN_POOLS,
    PLANES_DEMO,
    SEDE_CODES,
    SEDES_DEMO,
    TUTORS_PER_SEDE,
    availability_block,
    build_tutor_specs,
    normalize_name,
    validate_catalog,
)

SEED_LOCK_KEY = 0x43554550
TUTOR_CARGA_MAX_HORAS = 12
GROUP_HOURS = 20
GROUP_BLOCK_HOURS = 2
GROUP_CAPACITY = 30


class SeedConflict(RuntimeError):
    pass


@dataclass
class SeedResult:
    created: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    reused: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    warnings: list[str] = field(default_factory=list)
    sede_patterns: list[tuple[str, str]] = field(default_factory=list)
    tutor_emails: list[str] = field(default_factory=list)


def _create(result: SeedResult, key: str) -> None:
    result.created[key] += 1


def _reuse(result: SeedResult, key: str) -> None:
    result.reused[key] += 1


def _allocate_code(preferred: str, used_codes: set[str]) -> str:
    candidates = [preferred] + [code for code in SEDE_CODES if code != preferred]
    for code in candidates:
        if code and code not in used_codes:
            return code
    raise SeedConflict("No hay códigos de sede disponibles.")


def _resolve_password(dry_run: bool) -> str | None:
    if dry_run:
        return None
    password = os.environ.get(PASSWORD_ENV)
    if password is None:
        if not sys.stdin.isatty():
            raise SeedConflict(
                f"Define {PASSWORD_ENV} o ejecuta el seed en una terminal interactiva."
            )
        password = getpass.getpass("Contraseña compartida para tutores demo: ")
        confirmation = getpass.getpass("Confirmar contraseña: ")
        if password != confirmation:
            raise SeedConflict("Las contraseñas no coinciden.")
    if len(password) < 8:
        raise SeedConflict("La contraseña debe tener al menos 8 caracteres.")
    return password


async def _first_admin(db: AsyncSession) -> User | None:
    result = await db.execute(
        select(User)
        .where(User.role == "admin", User.deleted_at.is_(None))
        .order_by(User.id)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _seed_sedes(
    db: AsyncSession, result: SeedResult
) -> list[Sede]:
    sedes = list((await db.execute(select(Sede))).scalars().all())
    all_by_code = {sede.codigo: sede for sede in sedes if sede.codigo}
    all_by_name = {normalize_name(sede.nombre): sede for sede in sedes}
    used_codes = set(all_by_code)

    target: list[Sede] = []
    for spec in SEDES_DEMO:
        by_code = all_by_code.get(spec.codigo)
        if by_code is not None:
            if by_code.deleted_at is not None:
                raise SeedConflict(
                    f"La sede con código {spec.codigo} está eliminada lógicamente."
                )
            target.append(by_code)
            _reuse(result, "sedes")
            continue

        by_name = all_by_name.get(normalize_name(spec.nombre))
        if by_name is not None:
            if by_name.deleted_at is not None:
                raise SeedConflict(
                    f"La sede {spec.nombre!r} está eliminada lógicamente."
                )
            if not by_name.codigo:
                by_name.codigo = _allocate_code(spec.codigo, used_codes)
                used_codes.add(by_name.codigo)
            target.append(by_name)
            _reuse(result, "sedes")
            continue

        code = _allocate_code(spec.codigo, used_codes)
        sede = Sede(
            nombre=spec.nombre,
            codigo=code,
            ciudad=spec.ciudad,
            descripcion=spec.descripcion,
            activo=True,
        )
        db.add(sede)
        used_codes.add(code)
        target.append(sede)
        _create(result, "sedes")

    await db.flush()
    result.sede_patterns = [(sede.codigo or "", sede.nombre) for sede in target]
    return target


async def _seed_plans(
    db: AsyncSession, admin: User | None, result: SeedResult
) -> list[PlanEstudio]:
    plans = list((await db.execute(select(PlanEstudio))).scalars().all())
    all_by_key = {(plan.nombre, plan.nivel): plan for plan in plans}
    all_by_name: dict[str, list[PlanEstudio]] = defaultdict(list)
    for plan in plans:
        all_by_name[plan.nombre].append(plan)

    target: list[PlanEstudio] = []
    for spec in PLANES_DEMO:
        key = (spec.nombre, spec.nivel)
        existing = all_by_key.get(key)
        if existing is not None:
            if existing.deleted_at is not None:
                raise SeedConflict(f"El plan {spec.nombre!r} está eliminado lógicamente.")
            target.append(existing)
            _reuse(result, "planes")
            continue

        same_name = all_by_name.get(spec.nombre, [])
        if same_name:
            raise SeedConflict(
                f"El plan {spec.nombre!r} ya existe con otro nivel; revisa el catálogo."
            )

        plan = PlanEstudio(
            nombre=spec.nombre,
            nivel=spec.nivel,
            area=spec.area,
            descripcion=spec.descripcion or None,
            activo=True,
            created_by=admin.id if admin else None,
        )
        db.add(plan)
        target.append(plan)
        _create(result, "planes")

    await db.flush()
    return target


async def _seed_materias(
    db: AsyncSession,
    plans: list[PlanEstudio],
    result: SeedResult,
) -> dict[str, list[Materia]]:
    materias = list((await db.execute(select(Materia))).scalars().all())
    all_by_key = {(materia.nombre, materia.nivel): materia for materia in materias}
    plan_subjects: dict[str, list[Materia]] = defaultdict(list)

    for plan, spec in zip(plans, PLANES_DEMO, strict=True):
        for nombre in spec.materias:
            key = (nombre, spec.nivel)
            existing = all_by_key.get(key)
            if existing is not None:
                if existing.deleted_at is not None:
                    raise SeedConflict(
                        f"La materia {nombre!r} ({spec.nivel}) está eliminada lógicamente."
                    )
                materia = existing
                _reuse(result, "materias")
            else:
                catalog_item = MATERIA_BY_KEY[key]
                materia = Materia(
                    nombre=catalog_item.nombre,
                    nivel=catalog_item.nivel,
                    area=catalog_item.area,
                    descripcion="Materia demo para pruebas del CUEP.",
                )
                db.add(materia)
                all_by_key[key] = materia
                _create(result, "materias")
            plan_subjects[plan.nombre].append(materia)

    await db.flush()

    existing_links = {
        (plan_id, materia_id)
        for plan_id, materia_id in (await db.execute(select(plan_materias))).all()
    }
    new_links: list[dict[str, int]] = []
    for plan, spec in zip(plans, PLANES_DEMO, strict=True):
        for materia in plan_subjects[plan.nombre]:
            key = (plan.id, materia.id)
            if key in existing_links:
                _reuse(result, "plan_materias")
                continue
            existing_links.add(key)
            new_links.append({"plan_id": plan.id, "materia_id": materia.id})
            _create(result, "plan_materias")

    if new_links:
        await db.execute(insert(plan_materias), new_links)

    return plan_subjects


async def _seed_tutors(
    db: AsyncSession,
    sedes: list[Sede],
    plans: list[PlanEstudio],
    plan_subjects: dict[str, list[Materia]],
    password_hash: str,
    result: SeedResult,
) -> list[tuple[object, User]]:
    specs = build_tutor_specs([(sede.codigo or "", sede.nombre) for sede in sedes])
    sede_by_code = {sede.codigo or "": sede for sede in sedes}
    plan_by_name = {plan.nombre: plan for plan in plans}
    pools = [
        (plan_by_name[plan_name], area) for plan_name, area in PLAN_POOLS
    ]

    users = list((await db.execute(select(User))).scalars().all())
    users_by_email = {user.email.lower(): user for user in users}
    tutors: list[tuple[object, User]] = []

    for spec in specs:
        existing = users_by_email.get(spec.email.lower())
        if existing is not None:
            if existing.deleted_at is not None:
                raise SeedConflict(
                    f"El tutor {spec.email!r} está eliminado lógicamente."
                )
            if existing.role != "tutor" or not existing.es_tutor:
                raise SeedConflict(
                    f"El email {spec.email!r} existe pero no es un tutor."
                )
            expected_sede = sede_by_code[spec.sede_codigo]
            if existing.sede_id != expected_sede.id:
                raise SeedConflict(
                    f"El tutor {spec.email!r} pertenece a otra sede."
                )
            tutors.append((spec, existing))
            _reuse(result, "tutores")
            continue

        pool_plan, area = pools[spec.order % len(pools)]
        user = User(
            email=spec.email,
            password_hash=password_hash,
            nombre=spec.nombre[:100],
            apellido_paterno=spec.apellido_paterno[:100],
            apellido_materno=spec.apellido_materno[:100],
            role="tutor",
            sede_id=sede_by_code[spec.sede_codigo].id,
            es_tutor=True,
            carga_max_horas=TUTOR_CARGA_MAX_HORAS,
            area_principal=area,
            is_active=True,
        )
        db.add(user)
        tutors.append((spec, user))
        _create(result, "tutores")

    await db.flush()

    existing_tutor_materias = {
        (tutor_id, materia_id)
        for tutor_id, materia_id in (
            await db.execute(select(TutorMateria.tutor_id, TutorMateria.materia_id))
        ).all()
    }

    for spec, tutor in tutors:
        pool_plan, _ = pools[spec.order % len(pools)]
        subjects = plan_subjects[pool_plan.nombre]
        start = (spec.order // len(pools)) % len(subjects)
        selected = [
            subjects[(start + offset) % len(subjects)] for offset in range(3)
        ]
        for preference, materia in enumerate(selected, start=1):
            key = (tutor.id, materia.id)
            if key in existing_tutor_materias:
                _reuse(result, "tutor_materias")
                continue
            existing_tutor_materias.add(key)
            db.add(
                TutorMateria(
                    tutor_id=tutor.id,
                    materia_id=materia.id,
                    nivel_preferencia=preference,
                    vetada=False,
                )
            )
            _create(result, "tutor_materias")

    result.tutor_emails = [spec.email for spec, _ in tutors]
    return tutors


async def _seed_availability(
    db: AsyncSession,
    tutors: list[tuple[object, User]],
    *,
    skip_availability: bool,
    result: SeedResult,
) -> None:
    schedule = await cargar_horario(db)
    active_days = [day for day in schedule if day.activo]
    if not active_days:
        if skip_availability:
            result.warnings.append(
                "No hay días activos en el horario CUEP; se omitió la disponibilidad."
            )
            return
        raise SeedConflict(
            "No hay días activos en el horario CUEP; configura el horario o usa "
            "--skip-availability."
        )

    for day in active_days:
        if (
            day.hora_inicio.minute
            or day.hora_inicio.second
            or day.hora_fin.minute
            or day.hora_fin.second
        ):
            raise SeedConflict("El horario del CUEP debe estar en horas completas.")
        if day.hora_fin.hour <= day.hora_inicio.hour:
            raise SeedConflict(
                f"El día {day.dia_semana} no tiene un rango horario válido."
            )

    existing = {
        tutor_id
        for (tutor_id,) in (
            await db.execute(select(DisponibilidadTutor.tutor_id).distinct())
        ).all()
    }

    for spec, tutor in tutors:
        if tutor.id in existing:
            _reuse(result, "disponibilidad")
            continue

        if len(active_days) == 1:
            days = [active_days[0]]
        else:
            days = [
                active_days[spec.order % len(active_days)],
                active_days[(spec.order + 1) % len(active_days)],
            ]

        for offset, day in enumerate(days):
            block = availability_block(
                day.hora_inicio, day.hora_fin, spec.order, offset
            )
            if block is None:
                continue
            start, end = block
            db.add(
                DisponibilidadTutor(
                    tutor_id=tutor.id,
                    dia_semana=day.dia_semana,
                    hora_inicio=start,
                    hora_fin=end,
                )
            )
            _create(result, "disponibilidad")

    await db.flush()


async def _seed_groups(
    db: AsyncSession,
    sedes: list[Sede],
    plans: list[PlanEstudio],
    plan_subjects: dict[str, list[Materia]],
    result: SeedResult,
) -> None:
    groups = list((await db.execute(select(Grupo))).scalars().all())
    existing_by_key = {
        (group.sede_id, group.materia_id, normalize_name(group.nombre)): group
        for group in groups
    }

    for plan in plans:
        representante = plan_subjects[plan.nombre][0]
        group_name = f"{plan.nombre} - Grupo A"[:100]
        for sede in sedes:
            key = (sede.id, representante.id, normalize_name(group_name))
            existing = existing_by_key.get(key)
            if existing is not None:
                if existing.deleted_at is not None:
                    raise SeedConflict(
                        f"El grupo {group_name!r} de {sede.nombre!r} está eliminado."
                    )
                _reuse(result, "grupos")
                continue

            db.add(
                Grupo(
                    sede_id=sede.id,
                    materia_id=representante.id,
                    nombre=group_name,
                    horas_totales=GROUP_HOURS,
                    bloque_horas=GROUP_BLOCK_HOURS,
                    capacidad=GROUP_CAPACITY,
                    min_alumnos=0,
                )
            )
            _create(result, "grupos")

    await db.flush()


async def seed(
    db: AsyncSession,
    *,
    password_hash: str | None,
    dry_run: bool,
    skip_availability: bool,
) -> SeedResult:
    validate_catalog()
    result = SeedResult()
    await db.execute(
        text("SELECT pg_advisory_xact_lock(:key)"), {"key": SEED_LOCK_KEY}
    )

    admin = await _first_admin(db)
    sedes = await _seed_sedes(db, result)
    plans = await _seed_plans(db, admin, result)
    plan_subjects = await _seed_materias(db, plans, result)
    tutors = await _seed_tutors(
        db,
        sedes,
        plans,
        plan_subjects,
        password_hash or "dry-run-placeholder",
        result,
    )
    await _seed_availability(
        db,
        tutors,
        skip_availability=skip_availability,
        result=result,
    )
    await _seed_groups(db, sedes, plans, plan_subjects, result)
    return result


def _print_report(result: SeedResult, *, dry_run: bool) -> None:
    title = "Dry-run completado; no se escribió nada." if dry_run else "Seed completado."
    print(title)
    for key in (
        "sedes",
        "planes",
        "materias",
        "plan_materias",
        "tutores",
        "tutor_materias",
        "disponibilidad",
        "grupos",
    ):
        print(
            f"  {key}: creados={result.created[key]}, reutilizados={result.reused[key]}"
        )

    print("Patrones de acceso por sede:")
    for codigo, nombre in result.sede_patterns:
        print(f"  {nombre} ({codigo}): tutor-{codigo.lower()}-01..{TUTORS_PER_SEDE:02d}@{EMAIL_DOMAIN}")
    print("Todos los tutores demo comparten la contraseña configurada en el seed.")
    for warning in result.warnings:
        print(f"Advertencia: {warning}")


def _write_emails(path: Path, emails: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(emails) + "\n", encoding="utf-8")
    path.chmod(0o600)
    print(f"Emails de tutores escritos en {path}")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carga idempotente de sedes, tutores, planes y grupos demo."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida y reporta los cambios sin confirmar la transacción.",
    )
    parser.add_argument(
        "--skip-availability",
        action="store_true",
        help="No genera disponibilidad para los tutores demo.",
    )
    parser.add_argument(
        "--emails-file",
        type=Path,
        default=None,
        help="Guarda los 180 emails de tutores en un archivo con permisos 600.",
    )
    args = parser.parse_args()

    password = _resolve_password(args.dry_run)
    password_hash = get_password_hash(password) if password else None

    async with async_session_factory() as db:
        try:
            result = await seed(
                db,
                password_hash=password_hash,
                dry_run=args.dry_run,
                skip_availability=args.skip_availability,
            )
            if args.dry_run:
                await db.rollback()
            else:
                await db.commit()
        except Exception:
            await db.rollback()
            raise

    _print_report(result, dry_run=args.dry_run)
    if args.emails_file is not None and not args.dry_run:
        _write_emails(args.emails_file, result.tutor_emails)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SeedConflict as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
