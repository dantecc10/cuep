import asyncio
import csv
import io
import secrets
import string
import unicodedata
from typing import Literal, Optional

from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import allowed_import_roles
from app.core.security import get_password_hash
from app.models.materia import Materia
from app.models.plan import PlanEstudio
from app.models.sede import Sede
from app.models.user import User
from app.schemas.imports import (
    ImportCreatedRelated,
    ImportCredential,
    ImportReport,
    ImportRowIssue,
)
from app.services.email import send_email_sync

Entity = Literal["materias", "planes", "sedes", "usuarios"]

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 1000
NIVELES = {"PREPA", "LICENCIATURA"}

HEADER_ALIASES = {
    "correo": "email",
    "e_mail": "email",
    "rol": "role",
    "sede": "sede_codigo",
    "codigo_sede": "sede_codigo",
    "apellido1": "apellido_paterno",
    "apellido2": "apellido_materno",
    "nombre_completo": "nombre",
}

TRUE_VALUES = {"1", "true", "si", "sí", "yes", "x", "verdadero"}
FALSE_VALUES = {"0", "false", "no", "n", "falso"}

FIELD_LIMITS: dict[str, dict[str, int]] = {
    "materias": {"nombre": 100, "nivel": 20, "area": 50},
    "planes": {"nombre": 150, "nivel": 20, "area": 50},
    "sedes": {"nombre": 150, "ciudad": 100, "codigo": 1},
    "usuarios": {
        "email": 255,
        "nombre": 100,
        "apellido_paterno": 100,
        "apellido_materno": 100,
        "telefono": 30,
        "area_principal": 50,
    },
}


class CsvFormatError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)


def _normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _normalize_header(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.strip().lower().replace(" ", "_").replace("-", "_")
    return HEADER_ALIASES.get(value, value)


def _key(nombre: str, nivel: str) -> tuple[str, str]:
    return (nombre.strip().casefold(), nivel.strip().upper())


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"Valor booleano inválido: {value}")


def _parse_int(value: Optional[str], default: int = 0) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value.strip())


def _parse_email(value: str) -> str:
    try:
        return validate_email(value, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise ValueError(f"Email inválido: {exc}") from exc


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise CsvFormatError("No se pudo leer el archivo. Guarda el CSV en UTF-8.")


def _is_blank_row(row: dict[str, Optional[str]]) -> bool:
    return all(
        value is None or str(value).strip() == ""
        for key, value in row.items()
        if key is not None
    )


async def _read_rows(file: UploadFile, required: set[str]) -> list[dict[str, Optional[str]]]:
    raw = await file.read()
    if not raw:
        raise CsvFormatError("El archivo está vacío.")
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="El CSV no debe superar 5 MB.")

    text = _decode(raw)
    lines = text.splitlines()
    first_line = lines[0] if lines else ""
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        raise CsvFormatError("El CSV no tiene encabezados.")
    reader.fieldnames = [_normalize_header(name) for name in reader.fieldnames]
    missing = sorted(required - set(reader.fieldnames))
    if missing:
        raise CsvFormatError("Faltan columnas obligatorias: " + ", ".join(missing))

    rows: list[dict[str, Optional[str]]] = []
    for row in reader:
        if _is_blank_row(row):
            continue
        rows.append(row)
        if len(rows) > MAX_ROWS:
            raise HTTPException(
                status_code=413,
                detail=f"El CSV supera el límite de {MAX_ROWS} filas.",
            )
    return rows


def _add_error(report: ImportReport, row: int, message: str) -> None:
    report.fallidas += 1
    report.errores.append(ImportRowIssue(fila=row, mensaje=message))


def _add_warning(report: ImportReport, row: int, message: str) -> None:
    report.advertencias.append(ImportRowIssue(fila=row, mensaje=message))


def _friendly_db_error(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    if "stringdatarighttruncation" in name or "value too long" in text:
        return "Uno de los valores es demasiado largo para la base de datos."
    if "uniqueviolation" in name or "duplicate key" in text:
        return "Ya existe un registro con ese valor único (revisa el código o el correo)."
    if "notnullviolation" in name or "not-null" in text:
        return "Falta un dato obligatorio."
    if "foreignkeyviolation" in name or "foreign key" in text:
        return "El registro hace referencia a una sede o materia que no existe."
    if "checkviolation" in name or "check constraint" in text:
        return "Uno de los valores no cumple las reglas permitidas."
    return "No se pudo guardar la fila por un dato inválido. Revisa los valores e inténtalo de nuevo."


def _check_lengths(
    report: ImportReport,
    row: int,
    entity: str,
    values: dict[str, Optional[str]],
) -> bool:
    limits = FIELD_LIMITS.get(entity, {})
    valid = True
    for field, max_length in limits.items():
        value = values.get(field)
        if value is None:
            continue
        if len(str(value)) > max_length:
            _add_error(
                report,
                row,
                f"El campo '{field}' no puede superar {max_length} caracteres "
                f"(tiene {len(str(value))}).",
            )
            valid = False
    return valid


def _first_available_code(used_codes: set[str]) -> Optional[str]:
    for letter in string.ascii_uppercase:
        if letter not in used_codes:
            return letter
    return None


async def _import_materias(
    db: AsyncSession,
    rows: list[dict[str, Optional[str]]],
) -> ImportReport:
    report = ImportReport(entidad="materias", total=len(rows))
    result = await db.execute(select(Materia).where(Materia.deleted_at.is_(None)))
    by_key = {_key(materia.nombre, materia.nivel): materia for materia in result.scalars().all()}
    seen: set[tuple[str, str]] = set()

    for index, row in enumerate(rows, start=2):
        nombre = _normalize(row.get("nombre"))
        area = _normalize(row.get("area"))
        nivel = (_normalize(row.get("nivel")) or "").upper()
        if not nombre:
            _add_error(report, index, "El nombre es obligatorio.")
            continue
        if nivel not in NIVELES:
            _add_error(report, index, "El nivel debe ser PREPA o LICENCIATURA.")
            continue
        if not area:
            _add_error(report, index, "El área es obligatoria.")
            continue
        if not _check_lengths(report, index, "materias", {"nombre": nombre, "nivel": nivel, "area": area}):
            continue

        key = _key(nombre, nivel)
        if key in by_key or key in seen:
            report.omitidas += 1
            continue

        try:
            async with db.begin_nested():
                materia = Materia(
                    nombre=nombre,
                    nivel=nivel,
                    area=area,
                    descripcion=_normalize(row.get("descripcion")),
                )
                db.add(materia)
                await db.flush()
        except Exception as exc:  # noqa: BLE001
            _add_error(report, index, f"No se pudo crear la materia: {_friendly_db_error(exc)}")
            continue

        seen.add(key)
        by_key[key] = materia
        report.creadas += 1

    return report


async def _import_sedes(
    db: AsyncSession,
    rows: list[dict[str, Optional[str]]],
) -> ImportReport:
    report = ImportReport(entidad="sedes", total=len(rows))
    result = await db.execute(select(Sede))
    by_code = {sede.codigo.upper(): sede for sede in result.scalars().all() if sede.codigo}
    used_codes = set(by_code)

    for index, row in enumerate(rows, start=2):
        nombre = _normalize(row.get("nombre"))
        if not nombre:
            _add_error(report, index, "El nombre es obligatorio.")
            continue

        ciudad = _normalize(row.get("ciudad"))
        codigo = _normalize(row.get("codigo"))
        if codigo:
            codigo = codigo.upper()
            if len(codigo) != 1:
                _add_error(report, index, "El código debe ser exactamente un carácter.")
                continue
        else:
            codigo = _first_available_code(used_codes)
            if codigo is None:
                _add_error(report, index, "No hay códigos de una letra disponibles.")
                continue
            _add_warning(
                report,
                index,
                f"Código asignado automáticamente: {codigo}. Verifica que corresponda a la sede.",
            )

        if codigo in used_codes:
            report.omitidas += 1
            continue

        if not _check_lengths(report, index, "sedes", {"nombre": nombre, "ciudad": ciudad, "codigo": codigo}):
            continue

        try:
            activo = _parse_bool(row.get("activo"), default=True)
        except ValueError as exc:
            _add_error(report, index, str(exc))
            continue

        try:
            async with db.begin_nested():
                sede = Sede(
                    nombre=nombre,
                    ciudad=ciudad,
                    codigo=codigo,
                    descripcion=_normalize(row.get("descripcion")),
                    maps_url=_normalize(row.get("maps_url")),
                    image_url=_normalize(row.get("image_url")),
                    activo=activo,
                )
                db.add(sede)
                await db.flush()
        except Exception as exc:  # noqa: BLE001
            _add_error(report, index, f"No se pudo crear la sede: {_friendly_db_error(exc)}")
            continue

        used_codes.add(codigo)
        by_code[codigo] = sede
        report.creadas += 1

    return report


async def _import_planes(
    db: AsyncSession,
    rows: list[dict[str, Optional[str]]],
) -> ImportReport:
    report = ImportReport(entidad="planes", total=len(rows))
    plan_result = await db.execute(select(PlanEstudio).where(PlanEstudio.deleted_at.is_(None)))
    planes_by_key = {
        _key(plan.nombre, plan.nivel): plan for plan in plan_result.scalars().all()
    }
    materia_result = await db.execute(select(Materia).where(Materia.deleted_at.is_(None)))
    materias_by_key = {
        _key(materia.nombre, materia.nivel): materia
        for materia in materia_result.scalars().all()
    }
    seen: set[tuple[str, str]] = set()

    for index, row in enumerate(rows, start=2):
        nombre = _normalize(row.get("nombre"))
        nivel = (_normalize(row.get("nivel")) or "").upper()
        if not nombre:
            _add_error(report, index, "El nombre es obligatorio.")
            continue
        if nivel not in NIVELES:
            _add_error(report, index, "El nivel debe ser PREPA o LICENCIATURA.")
            continue

        key = _key(nombre, nivel)
        if key in planes_by_key or key in seen:
            report.omitidas += 1
            continue

        area = _normalize(row.get("area"))
        descripcion = _normalize(row.get("descripcion"))
        if not _check_lengths(report, index, "planes", {"nombre": nombre, "nivel": nivel, "area": area}):
            continue
        materias_raw = _normalize(row.get("materias"))
        materia_names = (
            [part.strip() for part in materias_raw.replace(",", ";").split(";") if part.strip()]
            if materias_raw
            else []
        )

        try:
            row_created_related: list[ImportCreatedRelated] = []
            new_materia_keys: list[tuple[str, str]] = []
            async with db.begin_nested():
                plan = PlanEstudio(
                    nombre=nombre,
                    nivel=nivel,
                    area=area,
                    descripcion=descripcion,
                )
                db.add(plan)
                await db.flush()

                materias: list[Materia] = []
                added_ids: set[int] = set()
                for materia_name in materia_names:
                    materia_key = _key(materia_name, nivel)
                    materia = materias_by_key.get(materia_key)
                    if materia is None:
                        materia = Materia(
                            nombre=materia_name,
                            nivel=nivel,
                            area=area or "General",
                            descripcion=None,
                        )
                        db.add(materia)
                        await db.flush()
                        materias_by_key[materia_key] = materia
                        new_materia_keys.append(materia_key)
                        row_created_related.append(
                            ImportCreatedRelated(
                                tipo="materia",
                                nombre=materia_name,
                                detalle=f"Creada desde el plan {nombre} (fila {index}).",
                            )
                        )
                    if materia.id not in added_ids:
                        materias.append(materia)
                        added_ids.add(materia.id)

                plan.materias = materias
                await db.flush()
        except Exception as exc:  # noqa: BLE001
            for materia_key in new_materia_keys:
                materias_by_key.pop(materia_key, None)
            _add_error(report, index, f"No se pudo crear el plan: {_friendly_db_error(exc)}")
            continue

        report.creadas_relacionadas.extend(row_created_related)
        seen.add(key)
        planes_by_key[key] = plan
        report.creadas += 1

    return report


async def _import_usuarios(
    db: AsyncSession,
    rows: list[dict[str, Optional[str]]],
    actor: User,
) -> ImportReport:
    report = ImportReport(entidad="usuarios", total=len(rows))
    allowed_roles = allowed_import_roles(actor.role)
    if not allowed_roles:
        raise HTTPException(status_code=403, detail="Rol no autorizado para importar usuarios.")

    user_result = await db.execute(select(User))
    existing_by_email = {user.email.casefold(): user for user in user_result.scalars().all()}

    sede_result = await db.execute(select(Sede))
    sedes = sede_result.scalars().all()
    sedes_by_code = {sede.codigo.upper(): sede for sede in sedes if sede.codigo}
    sedes_by_id = {sede.id: sede for sede in sedes}

    own_sede: Optional[Sede] = None
    if actor.role == "coordinador":
        if actor.sede_id is None:
            raise HTTPException(
                status_code=403,
                detail="Asigna una sede al coordinador antes de importar tutores.",
            )
        own_sede = sedes_by_id.get(actor.sede_id)
        if own_sede is None or not own_sede.codigo:
            raise HTTPException(
                status_code=403,
                detail="El coordinador no tiene una sede con código configurado.",
            )

    pending_emails: list[tuple[ImportCredential, str]] = []

    for index, row in enumerate(rows, start=2):
        email_raw = _normalize(row.get("email"))
        nombre = _normalize(row.get("nombre"))
        apellido_paterno = _normalize(row.get("apellido_paterno"))
        role = (_normalize(row.get("role")) or "tutor").lower()

        if not email_raw:
            _add_error(report, index, "El email es obligatorio.")
            continue
        if not nombre:
            _add_error(report, index, "El nombre es obligatorio.")
            continue
        if not apellido_paterno:
            _add_error(report, index, "El apellido paterno es obligatorio.")
            continue
        if role not in allowed_roles:
            _add_error(
                report,
                index,
                f"El rol {role} no está permitido para tu perfil. Roles permitidos: "
                + ", ".join(sorted(allowed_roles))
                + ".",
            )
            continue

        try:
            email = _parse_email(email_raw).lower()
        except ValueError as exc:
            _add_error(report, index, str(exc))
            continue

        if email.casefold() in existing_by_email:
            report.omitidas += 1
            continue

        sede: Optional[Sede] = None
        sede_codigo = _normalize(row.get("sede_codigo"))
        if own_sede is not None:
            if sede_codigo and sede_codigo.upper() != own_sede.codigo.upper():
                _add_error(
                    report,
                    index,
                    f"Solo puedes importar tutores para tu sede ({own_sede.codigo}).",
                )
                continue
            sede = own_sede
        elif sede_codigo:
            sede = sedes_by_code.get(sede_codigo.upper())
            if sede is None:
                _add_error(report, index, f"No existe una sede con código {sede_codigo}.")
                continue

        try:
            es_tutor = _parse_bool(row.get("es_tutor"), default=(role == "tutor"))
            carga_max_horas = _parse_int(row.get("carga_max_horas"), default=0)
        except ValueError as exc:
            _add_error(report, index, str(exc))
            continue
        if carga_max_horas < 0:
            _add_error(report, index, "La carga máxima no puede ser negativa.")
            continue

        apellido_materno = _normalize(row.get("apellido_materno"))
        telefono = _normalize(row.get("telefono"))
        area_principal = _normalize(row.get("area_principal"))
        if not _check_lengths(
            report,
            index,
            "usuarios",
            {
                "email": email,
                "nombre": nombre,
                "apellido_paterno": apellido_paterno,
                "apellido_materno": apellido_materno,
                "telefono": telefono,
                "area_principal": area_principal,
            },
        ):
            continue

        temporary_password = secrets.token_urlsafe(9)
        try:
            password_hash = await run_in_threadpool(get_password_hash, temporary_password)
            async with db.begin_nested():
                user = User(
                    email=email,
                    password_hash=password_hash,
                    nombre=nombre,
                    apellido_paterno=apellido_paterno,
                    apellido_materno=apellido_materno,
                    role=role,
                    sede_id=sede.id if sede else None,
                    es_tutor=es_tutor,
                    telefono=telefono,
                    area_principal=area_principal,
                    carga_max_horas=carga_max_horas,
                    is_active=True,
                )
                db.add(user)
                await db.flush()
        except Exception as exc:  # noqa: BLE001
            _add_error(report, index, f"No se pudo crear el usuario: {_friendly_db_error(exc)}")
            continue

        existing_by_email[email.casefold()] = user
        report.creadas += 1

        credential = ImportCredential(
            email=email,
            password_temporal=temporary_password,
            email_enviado=False,
        )
        report.credenciales.append(credential)
        pending_emails.append((credential, nombre))

    if pending_emails:
        semaphore = asyncio.Semaphore(5)

        async def send_credential(credential: ImportCredential, nombre: str) -> None:
            async with semaphore:
                credential.email_enviado = await run_in_threadpool(
                    send_email_sync,
                    credential.email,
                    "Acceso a CUEP",
                    (
                        f"Hola {nombre},\n\n"
                        "Se creó una cuenta para ti en el sistema CUEP.\n"
                        f"Usuario: {credential.email}\n"
                        f"Contraseña temporal: {credential.password_temporal}\n\n"
                        "Cambia tu contraseña después de iniciar sesión.\n"
                    ),
                )
            if credential.email_enviado:
                report.correos_enviados += 1
            else:
                report.correos_fallidos += 1

        await asyncio.gather(
            *(send_credential(credential, nombre) for credential, nombre in pending_emails)
        )

    return report


async def import_csv(
    entidad: Entity,
    file: UploadFile,
    db: AsyncSession,
    actor: User,
) -> ImportReport:
    if entidad == "materias":
        rows = await _read_rows(file, {"nombre", "nivel", "area"})
        return await _import_materias(db, rows)
    if entidad == "sedes":
        rows = await _read_rows(file, {"nombre"})
        return await _import_sedes(db, rows)
    if entidad == "planes":
        rows = await _read_rows(file, {"nombre", "nivel"})
        return await _import_planes(db, rows)
    if entidad == "usuarios":
        rows = await _read_rows(
            file,
            {"email", "nombre", "apellido_paterno", "role"},
        )
        return await _import_usuarios(db, rows, actor)
    raise CsvFormatError("Entidad de importación no válida.")


TEMPLATES: dict[str, tuple[list[str], list[list[str]]]] = {
    "sedes": (
        ["nombre", "ciudad", "codigo", "descripcion", "maps_url", "image_url", "activo"],
        [
            [
                "Sede Centro",
                "Ciudad de México",
                "A",
                "Sede principal del colectivo",
                "",
                "",
                "true",
            ]
        ],
    ),
    "materias": (
        ["nombre", "nivel", "area", "descripcion"],
        [["Álgebra", "PREPA", "Exactas", "Materia de ejemplo"]],
    ),
    "planes": (
        ["nombre", "nivel", "area", "descripcion", "materias"],
        [
            [
                "Plan Preparatoria 2026",
                "PREPA",
                "General",
                "Plan de ejemplo",
                "Álgebra;Biología",
            ]
        ],
    ),
    "usuarios": (
        [
            "email",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "role",
            "sede_codigo",
            "es_tutor",
            "telefono",
            "area_principal",
            "carga_max_horas",
        ],
        [
            [
                "tutor@example.com",
                "Ana",
                "García",
                "",
                "tutor",
                "A",
                "true",
                "5555555555",
                "Exactas",
                "10",
            ]
        ],
    ),
}


def build_template(entidad: Entity) -> str:
    headers, sample_rows = TEMPLATES[entidad]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(sample_rows)
    return "\ufeff" + buffer.getvalue()
