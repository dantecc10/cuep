import secrets
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.inscripcion import ConfiguracionInscripcion, EventoInscripcion
from app.models.pago import Cargo, Pago
from app.models.sede import Sede
from app.models.student import Student
from app.models.user import User
from app.schemas.inscripcion import InscripcionCreate
from app.services.matricula import generar_matricula
from app.services.normalization import (
    name_key,
    normalize_email,
    normalize_phone_mx,
    normalize_text,
    split_emergency_contact,
)
from app.services.pagos import calcular_saldo, crear_cargo_simulacro


class InscripcionError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def get_config(
    db: AsyncSession, for_update: bool = False
) -> ConfiguracionInscripcion:
    await db.execute(
        pg_insert(ConfiguracionInscripcion)
        .values(id=1, anio=datetime.now(timezone.utc).year)
        .on_conflict_do_nothing(index_elements=["id"])
    )
    stmt = select(ConfiguracionInscripcion).where(ConfiguracionInscripcion.id == 1)
    if for_update:
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    return result.scalar_one()


def pase_url(qr_token: str | None) -> str | None:
    if not qr_token:
        return None
    base = settings.PUBLIC_APP_URL.rstrip("/")
    return f"{base}/mi-registro?token={qr_token}"


def _identifier_token(value: str) -> str:
    raw = value.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        token = parse_qs(parsed.query).get("token")
        if token:
            return token[0]
        return parsed.path.rstrip("/").split("/")[-1]
    if "token=" in raw:
        token = parse_qs(raw.split("?", 1)[-1]).get("token")
        if token:
            return token[0]
    return raw


async def find_student_by_identifier(
    db: AsyncSession, identifier: str, include_deleted: bool = False
) -> Student | None:
    raw = _identifier_token(identifier)
    normalized = normalize_text(raw)
    if not normalized:
        return None
    conditions = [
        func.upper(Student.matricula) == normalized.upper(),
        Student.qr_token == normalized,
        func.lower(Student.email) == normalized.lower(),
    ]
    try:
        phone = normalize_phone_mx(normalized)
    except ValueError:
        phone = None
    if phone:
        conditions.append(Student.phone_normalized == phone)
    stmt = select(Student).where(or_(*conditions))
    if not include_deleted:
        stmt = stmt.where(Student.deleted_at.is_(None))
    result = await db.execute(stmt.order_by(Student.created_at.desc()).limit(1))
    return result.scalar_one_or_none()


async def register_inscripcion(
    db: AsyncSession, data: InscripcionCreate, registration_source: str = "web"
) -> tuple[User, Student, ConfiguracionInscripcion]:
    config = await get_config(db)
    if not config.registro_abierto:
        raise InscripcionError("El registro está cerrado por el momento.", 403)

    email = normalize_email(str(data.email))
    if not email:
        raise InscripcionError("El correo es obligatorio.", 422)

    sede = await db.get(Sede, data.sede_id)
    if sede is None or sede.deleted_at is not None or not sede.activo:
        raise InscripcionError("Sede no encontrada o inactiva.", 404)
    if not sede.codigo or len(sede.codigo.strip()) != 1:
        raise InscripcionError("La sede no tiene código de matrícula configurado.", 400)

    if data.preferred_sede_id is not None:
        preferred = await db.get(Sede, data.preferred_sede_id)
        if preferred is None or preferred.deleted_at is not None or not preferred.activo:
            raise InscripcionError("Sede preferida no encontrada o inactiva.", 404)

    try:
        phone_normalized = normalize_phone_mx(data.telefono)
    except ValueError as exc:
        raise InscripcionError(str(exc), 422) from exc

    user_exists = await db.execute(
        select(User.id).where(func.lower(User.email) == email).limit(1)
    )
    if user_exists.scalar_one_or_none() is not None:
        raise InscripcionError("Email ya registrado.", 409)
    student_exists = await db.execute(
        select(Student.id).where(func.lower(Student.email) == email).limit(1)
    )
    if student_exists.scalar_one_or_none() is not None:
        raise InscripcionError("Email ya registrado.", 409)
    if phone_normalized:
        phone_exists = await db.execute(
            select(Student.id).where(
                Student.phone_normalized == phone_normalized,
                Student.deleted_at.is_(None),
            ).limit(1)
        )
        if phone_exists.scalar_one_or_none() is not None:
            raise InscripcionError("Teléfono ya registrado.", 409)

    first_name = normalize_text(data.first_name or data.nombre)
    paternal = normalize_text(data.paternal_last_name or data.apellido_paterno)
    maternal = normalize_text(data.maternal_last_name or data.apellido_materno)
    full_name = normalize_text(
        data.full_name or " ".join(part for part in (first_name, paternal, maternal) if part)
    )
    if not name_key(full_name):
        raise InscripcionError("El nombre es obligatorio.", 422)

    emergency_name = normalize_text(data.emergency_contact_name)
    emergency_phone = normalize_text(data.emergency_contact_phone)
    if data.emergency_contact_raw and (not emergency_name or not emergency_phone):
        parsed_name, parsed_phone = split_emergency_contact(data.emergency_contact_raw)
        emergency_name = emergency_name or parsed_name
        emergency_phone = emergency_phone or parsed_phone

    now = datetime.now(timezone.utc)
    user = User(
        email=email,
        password_hash=get_password_hash(data.password),
        nombre=data.nombre.strip(),
        apellido_paterno=data.apellido_paterno.strip(),
        apellido_materno=normalize_text(data.apellido_materno),
        role="alumno",
        es_tutor=False,
        telefono=data.telefono,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    student = Student(
        user_id=user.id,
        email=email,
        sede_id=sede.id,
        preferred_sede_id=data.preferred_sede_id,
        nivel=data.nivel,
        area=normalize_text(data.area),
        estatus="registrado",
        anio=config.anio,
        phone_normalized=phone_normalized,
        qr_token=secrets.token_urlsafe(32),
        registration_source=registration_source,
        first_name=first_name,
        paternal_last_name=paternal,
        maternal_last_name=maternal,
        full_name=full_name,
        address=normalize_text(data.address),
        colony=normalize_text(data.colony),
        municipality_state=normalize_text(data.municipality_state),
        phone=data.telefono,
        emergency_contact_raw=normalize_text(data.emergency_contact_raw),
        emergency_contact_name=emergency_name,
        emergency_contact_phone=emergency_phone,
        high_school_type=normalize_text(data.high_school_type),
        exam_attempts=normalize_text(data.exam_attempts),
        desired_degree=normalize_text(data.desired_degree),
        study_area=normalize_text(data.study_area or data.area),
        diagnostic_exam=data.diagnostic_exam,
        donation_willingness=normalize_text(data.donation_willingness),
        presencial_consent=data.presencial_consent,
        credential_collected=data.credential_collected,
        preferred_course_location=normalize_text(data.preferred_course_location),
        photo_url=normalize_text(data.photo_url),
        form_submitted_at=data.form_submitted_at or now,
        notes=normalize_text(data.notes),
    )
    db.add(student)
    await db.flush()
    await generar_matricula(db, student, sede)

    db.add(
        EventoInscripcion(
            student_id=student.id,
            tipo="registro",
            estado_nuevo="registrado",
            sede_id=sede.id,
            detalle={"origen": registration_source, "solicita_simulacro": data.solicita_simulacro},
        )
    )

    if data.solicita_simulacro:
        await crear_cargo_simulacro(db, student, config)

    await db.flush()
    return user, student, config


async def get_inscripcion_me(db: AsyncSession, user: User) -> dict:
    result = await db.execute(
        select(Student).where(
            Student.user_id == user.id,
            Student.deleted_at.is_(None),
        )
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise InscripcionError("No tienes una inscripción registrada.", 404)

    cargos_result = await db.execute(
        select(Cargo)
        .where(Cargo.student_id == student.id, Cargo.deleted_at.is_(None))
        .order_by(Cargo.created_at.desc())
    )
    pagos_result = await db.execute(
        select(Pago)
        .where(Pago.student_id == student.id, Pago.deleted_at.is_(None))
        .order_by(Pago.created_at.desc())
    )
    eventos_result = await db.execute(
        select(EventoInscripcion)
        .where(EventoInscripcion.student_id == student.id)
        .order_by(EventoInscripcion.created_at.desc())
        .limit(30)
    )
    saldo = await calcular_saldo(db, student.id)
    return {
        "student": student,
        "cargos": cargos_result.scalars().all(),
        "pagos": pagos_result.scalars().all(),
        "eventos": eventos_result.scalars().all(),
        "saldo": float(Decimal(saldo)),
        "pase_url": pase_url(student.qr_token),
    }
