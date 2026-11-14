from __future__ import annotations

# ruff: noqa: E402

import argparse
import asyncio
import getpass
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import async_session_factory
from app.models.inscripcion import EventoInscripcion
from app.models.sede import Sede
from app.models.student import Student
from app.models.user import User
from app.schemas.inscripcion import InscripcionCreate
from app.services.inscripcion import InscripcionError, get_config, register_inscripcion
from app.services.normalization import extract_phone, name_key, normalize_text
from app.services.pagos import (
    PagoError,
    crear_cargo_simulacro,
    get_cargo_simulacro,
    registrar_pago,
)
from seeds.demo_catalog import SEDES_DEMO

SOURCE_FILE = BACKEND_DIR.parent / "sources" / "Copia de Lic CUEP 2026.xlsx"
EMAIL_DOMAIN = "cuep.example.com"
PASSWORD_ENV = "SEED_STUDENT_PASSWORD"
SEED_LOCK_KEY = 0x43554551
DEFAULT_LIMIT = 50
PAID_SIMULACRO_COUNT = 5

SEDE_BY_LOCATION_PREFIX = (
    ("1 ", "F"),
    ("2 ", "Z"),
    ("3 ", "2"),
    ("4 ", "C"),
    ("6 ", "L"),
    ("7 ", "V"),
)

AREA_MAP = {
    "ciencias naturales y salud": "Ciencias Naturales y de la Salud",
    "sociales y humanidades": "Ciencias Sociales",
    "economico administrativas": "Ciencias Sociales",
    "ingenierias y ciencias exactas": "Ingeniería y Ciencias Exactas",
}


STATUS_PLAN = (
    ["registrado"] * 25
    + ["en_inscripcion"] * 10
    + ["inscrito"] * 7
    + ["activo"] * 5
    + ["no_asistio"] * 3
)
CHECKED_IN_STATUSES = {"inscrito", "activo"}
CREDENTIAL_STATUSES = {"inscrito", "activo"}


class SeedConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceAspirante:
    source_index: int
    submitted_at: datetime | None
    nombre: str
    apellido_paterno: str
    apellido_materno: str | None
    address: str | None
    colony: str | None
    municipality_state: str | None
    phone: str | None
    emergency_contact_raw: str | None
    high_school_type: str | None
    exam_attempts: str | None
    preferred_course_location: str | None
    desired_degree: str | None
    area: str | None
    diagnostic_exam: bool
    donation_willingness: str | None
    presencial_consent: bool
    credential_collected: bool
    sede_code: str

    @property
    def email(self) -> str:
        return f"aspirante-{self.source_index:03d}@{EMAIL_DOMAIN}"

    def inscripcion(self, sede_id: int, *, solicita_simulacro: bool) -> InscripcionCreate:
        submitted = self.submitted_at
        if submitted is not None and submitted.tzinfo is None:
            submitted = submitted.replace(tzinfo=timezone.utc)
        return InscripcionCreate(
            email=self.email,
            password="seed-placeholder-password",
            nombre=self.nombre,
            apellido_paterno=self.apellido_paterno,
            apellido_materno=self.apellido_materno,
            telefono=self.phone,
            sede_id=sede_id,
            preferred_sede_id=sede_id,
            nivel="LICENCIATURA",
            area=self.area,
            study_area=self.area,
            address=self.address,
            colony=self.colony,
            municipality_state=self.municipality_state,
            emergency_contact_raw=self.emergency_contact_raw,
            high_school_type=self.high_school_type,
            exam_attempts=self.exam_attempts,
            desired_degree=self.desired_degree,
            diagnostic_exam=self.diagnostic_exam,
            donation_willingness=self.donation_willingness,
            presencial_consent=self.presencial_consent,
            credential_collected=self.credential_collected,
            preferred_course_location=self.preferred_course_location,
            form_submitted_at=submitted,
            notes=f"Registro demo generado a partir de la respuesta {self.source_index}.",
            solicita_simulacro=solicita_simulacro,
        )


def _clean(value: object, *, max_length: int | None = None) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        raw = str(int(value))
    elif isinstance(value, datetime):
        raw = value.isoformat()
    else:
        raw = str(value)
    normalized = normalize_text(raw)
    if normalized is None:
        return None
    return normalized[:max_length] if max_length else normalized


def _yes(value: object) -> bool:
    return (_clean(value) or "").casefold() in {"sí", "si", "yes", "1", "1.0"}


def canonical_area(value: object) -> str | None:
    raw = _clean(value)
    if raw is None:
        return None
    return AREA_MAP.get(name_key(raw), raw)


def sede_code_for_location(location: str | None) -> str | None:
    if not location:
        return None
    for prefix, code in SEDE_BY_LOCATION_PREFIX:
        if location.startswith(prefix):
            return code
    return None


def load_source_rows(path: Path = SOURCE_FILE) -> list[SourceAspirante]:
    try:
        import openpyxl
    except ImportError as exc:
        raise SeedConflict(
            "Falta openpyxl. Instala requirements.txt para ejecutar el seed."
        ) from exc

    if not path.exists():
        raise SeedConflict(f"No se encontró el archivo fuente: {path}")

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows: list[SourceAspirante] = []
    for index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=1):
        if len(row) < 19:
            continue
        nombre = _clean(row[1], max_length=100)
        apellido_paterno = _clean(row[2], max_length=100)
        if not nombre or not apellido_paterno:
            continue
        location = _clean(row[12], max_length=150)
        code = sede_code_for_location(location)
        if code is None:
            continue
        phone = extract_phone(row[7])
        rows.append(
            SourceAspirante(
                source_index=index,
                submitted_at=row[0] if isinstance(row[0], datetime) else None,
                nombre=nombre,
                apellido_paterno=apellido_paterno,
                apellido_materno=_clean(row[3], max_length=100),
                address=_clean(row[4]),
                colony=_clean(row[5], max_length=150),
                municipality_state=_clean(row[6], max_length=150),
                phone=phone,
                emergency_contact_raw=_clean(row[8]),
                high_school_type=_clean(row[10], max_length=20),
                exam_attempts=_clean(row[11], max_length=30),
                preferred_course_location=location,
                desired_degree=_clean(row[13], max_length=150),
                area=canonical_area(row[14]),
                diagnostic_exam=_yes(row[15]),
                donation_willingness=_clean(row[17], max_length=20),
                presencial_consent=_yes(row[18]),
                credential_collected=bool(row[19]),
                sede_code=code,
            )
        )
    if not rows:
        raise SeedConflict("El archivo fuente no contiene respuestas válidas.")
    return rows


def select_rows(rows: list[SourceAspirante], limit: int = DEFAULT_LIMIT) -> list[SourceAspirante]:
    if limit < 1:
        raise SeedConflict("El límite debe ser mayor a cero.")
    ordered = sorted(rows, key=lambda item: (item.submitted_at or datetime.min, item.source_index))
    by_location: dict[str, list[SourceAspirante]] = defaultdict(list)
    for row in ordered:
        by_location[row.sede_code].append(row)

    quota = max(1, limit // max(len(by_location), 1))
    selected: list[SourceAspirante] = []
    selected_ids: set[int] = set()
    for code in sorted(by_location):
        for row in by_location[code][:quota]:
            selected.append(row)
            selected_ids.add(row.source_index)

    for row in ordered:
        if len(selected) >= limit:
            break
        if row.source_index in selected_ids:
            continue
        selected.append(row)
        selected_ids.add(row.source_index)

    return sorted(selected, key=lambda item: (item.submitted_at or datetime.min, item.source_index))[:limit]


def _resolve_password(dry_run: bool) -> str | None:
    if dry_run:
        return None
    password = os.environ.get(PASSWORD_ENV)
    if password is None:
        if not sys.stdin.isatty():
            raise SeedConflict(
                f"Define {PASSWORD_ENV} o ejecuta el seed en una terminal interactiva."
            )
        password = getpass.getpass("Contraseña compartida para aspirantes demo: ")
        confirmation = getpass.getpass("Confirmar contraseña: ")
        if password != confirmation:
            raise SeedConflict("Las contraseñas no coinciden.")
    if len(password) < 8:
        raise SeedConflict("La contraseña debe tener al menos 8 caracteres.")
    return password


def _print_source_report(rows: list[SourceAspirante], selected: list[SourceAspirante]) -> None:
    print(f"Respuestas válidas en el archivo: {len(rows)}")
    print(f"Seleccionadas para el seed: {len(selected)}")
    for key, count in sorted(Counter(row.sede_code for row in selected).items()):
        print(f"  sede {key}: {count}")
    for key, count in sorted(Counter(row.area or "Sin área" for row in selected).items()):
        print(f"  área {key}: {count}")


async def _admin_id(db: AsyncSession) -> int | None:
    result = await db.execute(
        select(User.id).where(User.role == "admin", User.deleted_at.is_(None)).order_by(User.id).limit(1)
    )
    return result.scalar_one_or_none()


async def _ensure_sedes(db: AsyncSession) -> dict[str, Sede]:
    result = await db.execute(select(Sede).where(Sede.deleted_at.is_(None)))
    sedes = list(result.scalars().all())
    by_code = {sede.codigo: sede for sede in sedes if sede.codigo}
    by_name = {name_key(sede.nombre): sede for sede in sedes}

    for spec in SEDES_DEMO:
        if spec.codigo in by_code:
            if not by_code[spec.codigo].activo:
                raise SeedConflict(f"La sede con código {spec.codigo!r} está inactiva.")
            continue
        existing = by_name.get(name_key(spec.nombre))
        if existing is not None:
            if not existing.activo:
                raise SeedConflict(f"La sede {spec.nombre!r} está inactiva.")
            if existing.codigo and existing.codigo != spec.codigo:
                raise SeedConflict(
                    f"La sede {spec.nombre!r} ya existe con el código {existing.codigo!r}."
                )
            existing.codigo = spec.codigo
            by_code[spec.codigo] = existing
            continue
        sede = Sede(
            nombre=spec.nombre,
            codigo=spec.codigo,
            ciudad=spec.ciudad,
            descripcion=spec.descripcion,
            activo=True,
        )
        db.add(sede)
        sedes.append(sede)
        by_code[spec.codigo] = sede

    await db.flush()
    return {sede.codigo: sede for sede in sedes if sede.codigo and sede.activo}


async def seed(db: AsyncSession, rows: list[SourceAspirante], password: str, dry_run: bool) -> dict[str, object]:
    config = await get_config(db)
    if not config.registro_abierto:
        raise SeedConflict("El registro está cerrado en la configuración; ábrelo antes de seedear.")

    sedes = await _ensure_sedes(db)
    missing = sorted({row.sede_code for row in rows} - set(sedes))
    if missing:
        raise SeedConflict("No se pudieron preparar las sedes: " + ", ".join(missing))

    admin_id = await _admin_id(db)
    created = 0
    reused = 0
    skipped: list[str] = []
    seeded_students: list[Student] = []
    payment_candidates: list[Student] = []
    wants_simulacro = False

    for position, row in enumerate(rows):
        wants_simulacro = position % 3 == 0
        existing = await db.execute(
            select(Student).where(Student.email == row.email, Student.deleted_at.is_(None)).limit(1)
        )
        existing_student = existing.scalar_one_or_none()
        if existing_student is not None:
            if wants_simulacro:
                payment_candidates.append(existing_student)
            reused += 1
            continue

        user_exists = await db.execute(
            select(User.id).where(User.email == row.email).limit(1)
        )
        if user_exists.scalar_one_or_none() is not None:
            skipped.append(f"usuario existente sin alumno: {row.email}")
            continue

        payload = row.inscripcion(
            sedes[row.sede_code].id,
            solicita_simulacro=wants_simulacro,
        )
        updates: dict[str, object] = {"password": password}
        if row.phone:
            phone_exists = await db.execute(
                select(Student.id)
                .where(
                    Student.phone_normalized == row.phone,
                    Student.deleted_at.is_(None),
                )
                .limit(1)
            )
            if phone_exists.scalar_one_or_none() is not None:
                updates["telefono"] = None
                skipped.append(f"{row.email}: teléfono ya registrado; se omite el teléfono")
        payload = payload.model_copy(update=updates)
        try:
            _, student, _ = await register_inscripcion(
                db, payload, registration_source="seed"
            )
        except InscripcionError as exc:
            skipped.append(f"{row.email}: {exc.message}")
            continue

        target_status = STATUS_PLAN[min(position, len(STATUS_PLAN) - 1)]
        student.credential_collected = target_status in CREDENTIAL_STATUSES
        if target_status != student.estatus:
            previous = student.estatus
            student.estatus = target_status
            db.add(
                EventoInscripcion(
                    student_id=student.id,
                    tipo="cambio_estatus",
                    estado_anterior=previous,
                    estado_nuevo=target_status,
                    actor_id=admin_id,
                    sede_id=student.sede_id,
                    detalle={"origen": "seed"},
                )
            )

        if target_status in CHECKED_IN_STATUSES:
            checkin_at = (row.submitted_at or datetime.now(timezone.utc)) + timedelta(days=7)
            if checkin_at.tzinfo is None:
                checkin_at = checkin_at.replace(tzinfo=timezone.utc)
            student.checkin_at = checkin_at
            student.checkin_by = admin_id
            student.checkin_sede_id = student.sede_id
            db.add(
                EventoInscripcion(
                    student_id=student.id,
                    tipo="checkin",
                    estado_anterior=target_status,
                    estado_nuevo=target_status,
                    actor_id=admin_id,
                    sede_id=student.sede_id,
                    detalle={"origen": "seed"},
                )
            )

        seeded_students.append(student)
        if wants_simulacro:
            payment_candidates.append(student)
        created += 1

    if not dry_run:
        for student in payment_candidates[:PAID_SIMULACRO_COUNT]:
            cargo = await get_cargo_simulacro(db, student.id, config.anio)
            if cargo is None:
                cargo = await crear_cargo_simulacro(db, student, config, created_by=admin_id)
            if cargo is None:
                continue
            if cargo.estado == "pagado":
                continue
            if cargo.estado in {"cancelado", "exento"}:
                skipped.append(f"cargo no pagable para {student.email}: {cargo.estado}")
                continue
            try:
                await registrar_pago(
                    db,
                    student,
                    cargo,
                    monto=Decimal(cargo.monto),
                    metodo="efectivo",
                    config=config,
                    actor_id=admin_id,
                    referencia="SEED-DEMO",
                )
            except PagoError as exc:
                skipped.append(f"pago {student.email}: {exc.message}")

    return {
        "created": created,
        "reused": reused,
        "skipped": skipped,
        "year": config.anio,
        "students": seeded_students,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carga 50 aspirantes demo a partir del formulario real del CUEP."
    )
    parser.add_argument("--file", type=Path, default=SOURCE_FILE)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Sólo lee el Excel y reporta la selección; no escribe en la base.",
    )
    args = parser.parse_args()

    rows = load_source_rows(args.file)
    selected = select_rows(rows, args.limit)
    _print_source_report(rows, selected)

    password = _resolve_password(args.dry_run)
    if args.dry_run:
        print("Dry-run completado; no se escribió nada.")
        return

    assert password is not None
    async with async_session_factory() as db:
        try:
            await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": SEED_LOCK_KEY})
            result = await seed(db, selected, password, dry_run=False)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    print(
        f"Seed completado para el año {result['year']}: "
        f"creados={result['created']}, reutilizados={result['reused']}"
    )
    skipped = result["skipped"]
    for warning in skipped:
        print(f"Advertencia: {warning}")
    print("Todos los aspirantes demo comparten la contraseña configurada en el seed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SeedConflict as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
