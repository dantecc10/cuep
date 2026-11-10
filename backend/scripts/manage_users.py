#!/usr/bin/env python3
"""manage_users.py - Server-side CUEP user/account management CLI.

Emergency and maintenance helper to inspect and modify user accounts directly
against the CUEP database, without depending on the API or the web dashboard.

Cases it covers:
    * Password recovery when there is no admin access.
    * Role, sede and tutor-profile corrections.
    * Account activation, deactivation and soft deletion/restoration.
    * Two-factor authentication reset for locked-out users.
    * Linked student profile creation and correction.
    * Creating staff or student accounts during recovery.

Usage:
    python backend/scripts/manage_users.py
    python backend/scripts/manage_users.py list --search ana
    python backend/scripts/manage_users.py show --email ana@cuep.mx
    python backend/scripts/manage_users.py reset-password --email ana@cuep.mx
    python backend/scripts/manage_users.py set-password --email ana@cuep.mx
    python backend/scripts/manage_users.py activate --email ana@cuep.mx
    python backend/scripts/manage_users.py deactivate --email ana@cuep.mx --confirm
    python backend/scripts/manage_users.py set-role --email ana@cuep.mx --role coordinador
    python backend/scripts/manage_users.py set-sede --email ana@cuep.mx --sede-id 1
    python backend/scripts/manage_users.py delete --email ana@cuep.mx --confirm "DELETE ana@cuep.mx"
    python backend/scripts/manage_users.py restore --email ana@cuep.mx --activate
    python backend/scripts/manage_users.py reset-2fa --email ana@cuep.mx --confirm

Safety:
    * The target database host/port/name is printed before any write.
    * --dry-run shows the planned change and commits nothing.
    * Deactivation, 2FA reset and deletion require explicit confirmation.
    * Deletion requires the exact phrase "DELETE <email>".
    * Passwords are never printed except generated temporary passwords.
    * Password hashes and secrets are never printed.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import logging
import os
import secrets
import string
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from dotenv import load_dotenv
from sqlalchemy import delete, func, or_, select
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = BACKEND_ROOT / ".env"
MIN_PASSWORD_LENGTH = 8
DEFAULT_TEMP_PASSWORD_LENGTH = 16
VALID_ROLES = ("admin", "coordinador", "subcoordinador", "tutor", "alumno")
VALID_NIVELES = ("PREPA", "LICENCIATURA")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class _App:
    pass


_app: Optional[_App] = None
_VERBOSE = False


def _import_app() -> _App:
    global _app
    if _app is not None:
        return _app

    from app.core.config import settings
    from app.core.database import async_session_factory, engine
    from app.core.security import get_password_hash
    from app.models.sede import Sede
    from app.models.student import Enrollment, Student
    from app.models.two_factor import (
        RecoveryCode,
        TrustedDevice,
        TwoFactorAuditLog,
        TwoFactorChallenge,
    )
    from app.models.user import User
    from app.services.matricula import generar_matricula

    app = _App()
    app.settings = settings
    app.async_session_factory = async_session_factory
    app.engine = engine
    app.User = User
    app.Student = Student
    app.Enrollment = Enrollment
    app.Sede = Sede
    app.RecoveryCode = RecoveryCode
    app.TwoFactorChallenge = TwoFactorChallenge
    app.TrustedDevice = TrustedDevice
    app.TwoFactorAuditLog = TwoFactorAuditLog
    app.get_password_hash = get_password_hash
    app.generar_matricula = generar_matricula

    if not _VERBOSE:
        try:
            engine.echo = False
        except Exception:
            pass
        try:
            engine.pool.echo = False
        except Exception:
            pass

    _app = app
    return app


def _out(message: str = "") -> None:
    print(message)


def _reconfigure_stdio() -> None:
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


class _InputAborted(Exception):
    pass


def _read_input(prompt: str) -> str:
    while True:
        try:
            return input(prompt)
        except UnicodeDecodeError:
            _out("[aviso] Entrada no decodificable; intenta de nuevo.")
        except (EOFError, KeyboardInterrupt):
            raise _InputAborted()


def _getpass(prompt: str) -> str:
    while True:
        try:
            return getpass.getpass(prompt)
        except UnicodeDecodeError:
            _out("[aviso] Entrada no decodificable; intenta de nuevo.")
        except (EOFError, KeyboardInterrupt):
            raise _InputAborted()


def _configure_output(verbose: bool) -> None:
    if verbose:
        return
    for name in (
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
        "sqlalchemy.orm",
        "asyncpg",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def _normalize_sync_url(url: str) -> str:
    return (
        url.replace("postgresql+asyncpg://", "postgresql://", 1)
        .replace("postgresql+psycopg2://", "postgresql://", 1)
    )


def _safe_endpoint(url: str) -> str:
    try:
        parsed = make_url(_normalize_sync_url(url))
    except Exception:
        return "URL inválida"
    host = parsed.host or "unknown"
    port = parsed.port or "default"
    database = parsed.database or "unknown"
    username = parsed.username or "unknown"
    return f"{username}@{host}:{port}/{database}"


def _print_target_banner(url: str) -> None:
    _out(f"[target] {_safe_endpoint(url)}")


def _generate_password(length: int = DEFAULT_TEMP_PASSWORD_LENGTH) -> str:
    if length < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"La longitud mínima de contraseña es {MIN_PASSWORD_LENGTH}."
        )
    alphabet = string.ascii_letters + string.digits + "!@#$%&*+-_"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in "!@#$%&*+-_" for char in password)
        ):
            return password


def _prompt_new_password() -> str:
    while True:
        try:
            first = _getpass("Nueva contraseña: ")
            if len(first) < MIN_PASSWORD_LENGTH:
                _out(
                    f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
                )
                continue
            second = _getpass("Repite la contraseña: ")
        except _InputAborted:
            raise SystemExit("Cancelado.")
        if first != second:
            _out("Las contraseñas no coinciden. Intenta de nuevo.")
            continue
        return first


def _interactive_confirm(prompt: str) -> bool:
    try:
        answer = _read_input(f"{prompt} [y/N]: ").strip().lower()
    except _InputAborted:
        return False
    return answer in {"y", "yes", "s", "si", "sí"}


def _require_confirm_flag(args: argparse.Namespace, command: str) -> None:
    if getattr(args, "confirm", False):
        return
    raise SystemExit(f"Operación destructiva. Repite con --confirm para '{command}'.")


def _normalize_role(value: str) -> str:
    aliases = {
        "estudiante": "alumno",
        "student": "alumno",
        "coordinación": "coordinador",
        "coordinacion": "coordinador",
        "subcoordinación": "subcoordinador",
        "subcoordinacion": "subcoordinador",
        "administrador": "admin",
    }
    role = aliases.get(value.strip().lower(), value.strip().lower())
    if role not in VALID_ROLES:
        raise SystemExit(
            f"Rol inválido: {value!r}. Válidos: {', '.join(VALID_ROLES)}."
        )
    return role


def _normalize_nivel(value: str) -> str:
    aliases = {
        "preparatoria": "PREPA",
        "prepa": "PREPA",
        "licenciatura": "LICENCIATURA",
    }
    nivel = aliases.get(value.strip().lower(), value.strip().upper())
    if nivel not in VALID_NIVELES:
        raise SystemExit(
            f"Nivel inválido: {value!r}. Válidos: {', '.join(VALID_NIVELES)}."
        )
    return nivel


def _display_name(user: Any) -> str:
    parts = [user.nombre, user.apellido_paterno, user.apellido_materno]
    return " ".join(part for part in parts if part) or user.email


def _print_users_table(rows: Sequence[Any]) -> None:
    if not rows:
        _out("(sin resultados)")
        return
    header = (
        f"{'ID':>6}  {'EMAIL':<36} {'NOMBRE':<28} {'ROL':<15} "
        f"{'SEDE':<6} {'TUT':<4} {'ACT':<4} {'MATRICULA':<14} {'ELIM':<4}"
    )
    _out(header)
    _out("-" * len(header))
    for user, student in rows:
        _out(
            f"{user.id:>6}  {str(user.email or ''):<36.36} "
            f"{_display_name(user):<28.28} {str(user.role or ''):<15.15} "
            f"{str(user.sede_id if user.sede_id is not None else '-'):<6} "
            f"{'si' if user.es_tutor else 'no':<4} "
            f"{'si' if user.is_active else 'no':<4} "
            f"{str((student.matricula if student else None) or '-'):<14.14} "
            f"{'si' if user.deleted_at else 'no':<4}"
        )


def _print_student_detail(student: Any) -> None:
    _out(f"Student ID:    {student.id}")
    _out(f"Matrícula:     {student.matricula or '-'}")
    _out(f"Folio:         {student.folio if student.folio is not None else '-'}")
    _out(f"Nivel:         {student.nivel}")
    _out(f"Área:          {student.area or '-'}")
    _out(f"Estatus:       {student.estatus}")
    _out(f"Sede:          {student.sede_id if student.sede_id is not None else '-'}")
    _out(
        f"Sede preferida: {student.preferred_sede_id if student.preferred_sede_id is not None else '-'}"
    )
    _out(f"Email:         {student.email or '-'}")
    _out(f"Teléfono:      {student.phone or '-'}")
    _out(f"Notas:         {student.notes or '-'}")
    _out(f"Eliminado:     {student.deleted_at or '-'}")


def _print_user_detail(user: Any, student: Any, enrollment_count: int = 0) -> None:
    _out(f"ID:             {user.id}")
    _out(f"Email:          {user.email}")
    _out(f"Nombre:         {_display_name(user)}")
    _out(f"Rol:            {user.role}")
    _out(f"Sede:           {user.sede_id if user.sede_id is not None else '-'}")
    _out(f"Es tutor:       {user.es_tutor}")
    _out(f"Teléfono:       {user.telefono or '-'}")
    _out(f"Área principal: {user.area_principal or '-'}")
    _out(f"Carga máxima:   {user.carga_max_horas} h")
    _out(f"Foto URL:       {user.foto_url or '-'}")
    _out(f"Biografía:      {user.biografia_md or '-'}")
    _out(f"Activo:         {user.is_active}")
    _out(f"2FA:            {'activado' if user.totp_enabled else 'desactivado'}")
    _out(f"Creado:         {user.created_at}")
    _out(f"Actualizado:    {user.updated_at}")
    _out(f"Eliminado:      {user.deleted_at or '-'}")
    if student is not None:
        _out("")
        _out("Perfil de estudiante:")
        _print_student_detail(student)
        _out(f"Inscripciones:  {enrollment_count}")


def _print_sedes_table(sedes: Sequence[Any]) -> None:
    if not sedes:
        _out("(sin sedes)")
        return
    header = f"{'ID':>6}  {'NOMBRE':<32} {'CÓDIGO':<8} {'CIUDAD':<24} {'ACTIVA':<6} {'ELIM':<4}"
    _out(header)
    _out("-" * len(header))
    for sede in sedes:
        _out(
            f"{sede.id:>6}  {str(sede.nombre or ''):<32.32} "
            f"{str(sede.codigo or '-'):<8.8} {str(sede.ciudad or '-'):<24.24} "
            f"{'si' if sede.activo else 'no':<6} {'si' if sede.deleted_at else 'no':<4}"
        )


def _print_changes(changes: dict[str, Any]) -> None:
    _out("[cambios]")
    for key, value in changes.items():
        _out(f"  {key}: {'(vacío)' if value is None else value}")


async def _select_user(
    db: Any,
    *,
    email: Optional[str] = None,
    user_id: Optional[int] = None,
    include_deleted: bool = False,
) -> Any:
    app = _import_app()
    query = select(app.User)
    if user_id is not None:
        query = query.where(app.User.id == user_id)
    elif email:
        query = query.where(func.lower(app.User.email) == email.strip().lower())
    else:
        raise SystemExit("Especifica --email o --id.")
    if not include_deleted:
        query = query.where(app.User.deleted_at.is_(None))
    return (await db.execute(query)).scalar_one_or_none()


async def _select_student(db: Any, user_id: int, include_deleted: bool = True) -> Any:
    app = _import_app()
    query = select(app.Student).where(app.Student.user_id == user_id)
    if not include_deleted:
        query = query.where(app.Student.deleted_at.is_(None))
    return (await db.execute(query)).scalar_one_or_none()


async def _list_users(
    db: Any,
    *,
    search: Optional[str] = None,
    role: Optional[str] = None,
    active_only: bool = False,
    include_deleted: bool = False,
    limit: int = 100,
) -> Sequence[Any]:
    app = _import_app()
    query = select(app.User, app.Student).outerjoin(
        app.Student, app.Student.user_id == app.User.id
    )
    if not include_deleted:
        query = query.where(app.User.deleted_at.is_(None))
    if active_only:
        query = query.where(app.User.is_active.is_(True))
    if role:
        query = query.where(app.User.role == role)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                app.User.email.ilike(pattern),
                app.User.nombre.ilike(pattern),
                app.User.apellido_paterno.ilike(pattern),
                app.User.apellido_materno.ilike(pattern),
                app.User.telefono.ilike(pattern),
            )
        )
    query = query.order_by(app.User.id).limit(limit)
    return (await db.execute(query)).all()


async def _get_sede(db: Any, sede_id: int) -> Any:
    app = _import_app()
    sede = await db.get(app.Sede, sede_id)
    if sede is None or sede.deleted_at is not None:
        raise SystemExit(f"Sede no encontrada o eliminada: {sede_id}")
    return sede


async def _email_taken(db: Any, email: str, exclude_user_id: Optional[int] = None) -> bool:
    app = _import_app()
    query = select(app.User).where(func.lower(app.User.email) == email.strip().lower())
    if exclude_user_id is not None:
        query = query.where(app.User.id != exclude_user_id)
    return (await db.execute(query)).scalar_one_or_none() is not None


async def cmd_list(db: Any, args: argparse.Namespace) -> None:
    role = _normalize_role(args.role) if args.role else None
    rows = await _list_users(
        db,
        search=args.search,
        role=role,
        active_only=args.active_only,
        include_deleted=args.all,
        limit=args.limit,
    )
    _print_users_table(rows)


async def cmd_show(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    user = await _select_user(
        db, email=args.email, user_id=args.id, include_deleted=args.all
    )
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    student = await _select_student(db, user.id, include_deleted=True)
    enrollment_count = 0
    if student is not None:
        enrollment_count = int(
            (
                await db.execute(
                    select(func.count(app.Enrollment.id)).where(
                        app.Enrollment.student_id == student.id,
                        app.Enrollment.deleted_at.is_(None),
                    )
                )
            ).scalar()
            or 0
        )
    _print_user_detail(user, student, enrollment_count)


async def cmd_sedes(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    query = select(app.Sede).order_by(app.Sede.id)
    if not args.all:
        query = query.where(app.Sede.deleted_at.is_(None))
    _print_sedes_table((await db.execute(query)).scalars().all())


async def cmd_create(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    role = _normalize_role(args.role)
    if await _email_taken(db, args.email):
        raise SystemExit(f"Ya existe un usuario con email {args.email}.")
    if args.sede_id is not None:
        await _get_sede(db, args.sede_id)

    generated = False
    password = args.password
    if password is None and args.generate_password:
        password = _generate_password()
        generated = True
    if password is None and not args.dry_run:
        password = _prompt_new_password()
    if password is not None and len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
        )

    changes = {
        "email": args.email,
        "nombre": args.nombre,
        "apellido_paterno": args.apellido_paterno,
        "apellido_materno": args.apellido_materno,
        "role": role,
        "sede_id": args.sede_id,
        "es_tutor": args.es_tutor,
    }
    if args.dry_run:
        _print_changes(changes)
        _out("[dry-run] Crearía el usuario. No se escribió nada.")
        return

    user = app.User(
        email=args.email.strip(),
        password_hash=app.get_password_hash(password),
        nombre=args.nombre,
        apellido_paterno=args.apellido_paterno,
        apellido_materno=args.apellido_materno,
        role=role,
        sede_id=args.sede_id,
        es_tutor=args.es_tutor,
        telefono=args.telefono,
        area_principal=args.area_principal,
        carga_max_horas=args.carga_max_horas,
        biografia_md=args.biografia,
        foto_url=args.foto_url,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.commit()
    _out(f"Usuario creado: id={user.id} email={user.email} rol={user.role}.")
    if generated:
        _out(f"Contraseña temporal: {password}")
        _out("Compártela por un canal seguro.")


async def cmd_create_student(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    if await _email_taken(db, args.email):
        raise SystemExit(f"Ya existe un usuario con email {args.email}.")
    existing_student = (
        await db.execute(
            select(app.Student).where(
                func.lower(app.Student.email) == args.email.strip().lower()
            )
        )
    ).scalar_one_or_none()
    if existing_student is not None:
        raise SystemExit(f"Ya existe un perfil de estudiante con email {args.email}.")
    sede = await _get_sede(db, args.sede_id)
    nivel = _normalize_nivel(args.nivel)

    generated = False
    password = args.password
    if password is None and args.generate_password:
        password = _generate_password()
        generated = True
    if password is None and not args.dry_run:
        password = _prompt_new_password()
    if password is not None and len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres."
        )

    changes = {
        "email": args.email,
        "nombre": args.nombre,
        "apellido_paterno": args.apellido_paterno,
        "apellido_materno": args.apellido_materno,
        "role": "alumno",
        "sede_id": sede.id,
        "nivel": nivel,
        "area": args.area,
        "estatus": args.estatus,
    }
    if args.dry_run:
        _print_changes(changes)
        _out("[dry-run] Crearía usuario + perfil de estudiante. No se escribió nada.")
        return

    user = app.User(
        email=args.email.strip(),
        password_hash=app.get_password_hash(password),
        nombre=args.nombre,
        apellido_paterno=args.apellido_paterno,
        apellido_materno=args.apellido_materno,
        role="alumno",
        es_tutor=False,
        telefono=args.telefono,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    student = app.Student(
        user_id=user.id,
        email=user.email,
        sede_id=sede.id,
        nivel=nivel,
        area=args.area,
        estatus=args.estatus,
        first_name=args.nombre,
        paternal_last_name=args.apellido_paterno,
        maternal_last_name=args.apellido_materno,
        full_name=_display_name(user),
        phone=args.telefono,
        notes=args.notes,
    )
    db.add(student)
    await db.flush()

    if sede.codigo and len(sede.codigo) == 1:
        await app.generar_matricula(db, student, sede)
    else:
        _out(
            f"[aviso] La sede {sede.id} no tiene código de matrícula; "
            "el estudiante quedó sin matrícula."
        )
    await db.commit()
    _out(
        f"Estudiante creado: id={user.id} email={user.email} "
        f"student_id={student.id} matrícula={student.matricula or '-'}."
    )
    if generated:
        _out(f"Contraseña temporal: {password}")
        _out("Compártela por un canal seguro.")


async def cmd_update(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")

    changes: dict[str, Any] = {}
    if args.new_email is not None:
        if await _email_taken(db, args.new_email, exclude_user_id=user.id):
            raise SystemExit(f"Ya existe otro usuario con email {args.new_email}.")
        changes["email"] = args.new_email.strip()
    if args.nombre is not None:
        changes["nombre"] = args.nombre
    if args.apellido_paterno is not None:
        changes["apellido_paterno"] = args.apellido_paterno
    if args.clear_apellido_materno:
        changes["apellido_materno"] = None
    elif args.apellido_materno is not None:
        changes["apellido_materno"] = args.apellido_materno
    if args.clear_sede:
        changes["sede_id"] = None
    elif args.sede_id is not None:
        await _get_sede(db, args.sede_id)
        changes["sede_id"] = args.sede_id
    if args.role is not None:
        changes["role"] = _normalize_role(args.role)
    if args.es_tutor is not None:
        changes["es_tutor"] = args.es_tutor
    if args.clear_telefono:
        changes["telefono"] = None
    elif args.telefono is not None:
        changes["telefono"] = args.telefono
    if args.clear_area_principal:
        changes["area_principal"] = None
    elif args.area_principal is not None:
        changes["area_principal"] = args.area_principal
    if args.carga_max_horas is not None:
        changes["carga_max_horas"] = args.carga_max_horas
    if args.clear_biografia:
        changes["biografia_md"] = None
    elif args.biografia is not None:
        changes["biografia_md"] = args.biografia
    if args.clear_foto_url:
        changes["foto_url"] = None
    elif args.foto_url is not None:
        changes["foto_url"] = args.foto_url

    if not changes:
        raise SystemExit("Nada que actualizar.")
    if args.dry_run:
        _print_changes(changes)
        _out(f"[dry-run] Actualizaría a {user.email}. No se escribió nada.")
        return

    for field, value in changes.items():
        setattr(user, field, value)
    await db.flush()
    await db.commit()
    _out(f"Usuario actualizado: {user.email}.")
    _print_changes(changes)


async def cmd_set_role(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    role = _normalize_role(args.role)
    if user.role == role:
        _out(f"{user.email} ya tiene el rol {role}.")
        return
    if args.dry_run:
        _out(f"[dry-run] Cambiaría rol de {user.email}: {user.role} -> {role}.")
        return
    previous = user.role
    user.role = role
    await db.flush()
    await db.commit()
    _out(f"Rol actualizado para {user.email}: {previous} -> {role}.")


async def cmd_set_sede(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if args.none:
        new_sede = None
    else:
        if args.sede_id is None:
            raise SystemExit("Especifica --sede-id o --none.")
        sede = await _get_sede(db, args.sede_id)
        new_sede = sede.id
    if user.sede_id == new_sede:
        _out(f"{user.email} ya tiene sede_id={new_sede}.")
        return
    if args.dry_run:
        _out(f"[dry-run] Cambiaría sede de {user.email}: {user.sede_id} -> {new_sede}.")
        return
    previous = user.sede_id
    user.sede_id = new_sede
    await db.flush()
    await db.commit()
    _out(f"Sede actualizada para {user.email}: {previous} -> {new_sede}.")


async def cmd_set_tutor(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if user.es_tutor == args.enabled:
        _out(f"{user.email} ya tiene es_tutor={args.enabled}.")
        return
    if args.dry_run:
        _out(f"[dry-run] Cambiaría es_tutor de {user.email} a {args.enabled}.")
        return
    user.es_tutor = args.enabled
    await db.flush()
    await db.commit()
    _out(f"es_tutor actualizado para {user.email}: {args.enabled}.")


async def cmd_reset_password(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if args.dry_run:
        _out(f"[dry-run] Generaría contraseña temporal para {user.email}.")
        return
    password = _generate_password(args.length)
    user.password_hash = app.get_password_hash(password)
    await db.flush()
    await db.commit()
    _out(f"Contraseña restablecida para {user.email}.")
    _out(f"Contraseña temporal: {password}")
    _out("Compártela por un canal seguro.")


async def cmd_set_password(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if args.dry_run:
        _out(f"[dry-run] Asignaría una nueva contraseña a {user.email}.")
        return
    password = _prompt_new_password()
    user.password_hash = app.get_password_hash(password)
    await db.flush()
    await db.commit()
    _out(f"Contraseña actualizada para {user.email}.")


async def cmd_activate(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if user.is_active:
        _out(f"{user.email} ya está activo.")
        return
    if args.dry_run:
        _out(f"[dry-run] Activaría a {user.email}.")
        return
    user.is_active = True
    await db.flush()
    await db.commit()
    _out(f"Cuenta activada: {user.email}.")


async def cmd_deactivate(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if not user.is_active:
        _out(f"{user.email} ya está inactivo.")
        return
    _require_confirm_flag(args, "deactivate")
    if args.dry_run:
        _out(f"[dry-run] Desactivaría a {user.email}.")
        return
    user.is_active = False
    await db.flush()
    await db.commit()
    _out(f"Cuenta desactivada: {user.email}.")


async def cmd_delete(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    user = await _select_user(
        db, email=args.email, user_id=args.id, include_deleted=True
    )
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if user.deleted_at is not None:
        raise SystemExit(f"{user.email} ya está eliminado. Usa restore.")
    expected = f"DELETE {user.email}"
    if args.dry_run:
        extra = " y su perfil de estudiante" if args.include_student else ""
        _out(f"[dry-run] Eliminaría (soft-delete) a {user.email}{extra}.")
        return
    if args.confirm != expected:
        raise SystemExit(
            f'Confirmación incorrecta. Usa: --confirm "{expected}"'
        )
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    if args.include_student:
        student = await _select_student(db, user.id, include_deleted=False)
        if student is not None:
            student.deleted_at = datetime.now(timezone.utc)
            student.estatus = "inactivo"
            enrollments = (
                await db.execute(
                    select(app.Enrollment).where(
                        app.Enrollment.student_id == student.id,
                        app.Enrollment.deleted_at.is_(None),
                        app.Enrollment.estado != "cancelada",
                    )
                )
            ).scalars().all()
            for enrollment in enrollments:
                enrollment.estado = "cancelada"
    await db.flush()
    await db.commit()
    _out(f"Usuario eliminado (soft-delete): {user.email}.")


async def cmd_restore(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(
        db, email=args.email, user_id=args.id, include_deleted=True
    )
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if user.deleted_at is None:
        raise SystemExit(f"{user.email} no está eliminado.")
    if args.dry_run:
        _out(f"[dry-run] Restauraría a {user.email}.")
        return
    user.deleted_at = None
    if args.activate:
        user.is_active = True
    if args.include_student:
        student = await _select_student(db, user.id, include_deleted=True)
        if student is not None:
            student.deleted_at = None
            if student.estatus == "inactivo":
                student.estatus = "activo"
    await db.flush()
    await db.commit()
    _out(f"Usuario restaurado: {user.email} (activo={user.is_active}).")


async def cmd_reset_2fa(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    _require_confirm_flag(args, "reset-2fa")
    if args.dry_run:
        _out(f"[dry-run] Resetearía 2FA de {user.email}.")
        return
    user.totp_enabled = False
    user.totp_secret = None
    for model in (
        app.RecoveryCode,
        app.TwoFactorChallenge,
        app.TrustedDevice,
    ):
        await db.execute(delete(model).where(model.user_id == user.id))
    await db.flush()
    await db.commit()
    _out(f"2FA reseteado para {user.email}.")


async def cmd_student_show(db: Any, args: argparse.Namespace) -> None:
    user = await _select_user(
        db, email=args.email, user_id=args.id, include_deleted=True
    )
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    student = await _select_student(db, user.id, include_deleted=True)
    if student is None:
        raise SystemExit("El usuario no tiene perfil de estudiante.")
    _out(f"Usuario: {user.email} ({user.id})")
    _print_student_detail(student)


async def cmd_student_create(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    if user.role != "alumno":
        raise SystemExit(
            f"{user.email} tiene rol {user.role}. Usa set-role --role alumno primero."
        )
    existing = await _select_student(db, user.id, include_deleted=True)
    if existing is not None:
        raise SystemExit("El usuario ya tiene perfil de estudiante.")
    if args.sede_id is None:
        raise SystemExit("Especifica --sede-id.")
    sede = await _get_sede(db, args.sede_id)
    nivel = _normalize_nivel(args.nivel)
    if args.dry_run:
        _out(
            f"[dry-run] Crearía perfil de estudiante para {user.email} "
            f"(sede={sede.id}, nivel={nivel})."
        )
        return
    student = app.Student(
        user_id=user.id,
        email=user.email,
        sede_id=sede.id,
        nivel=nivel,
        area=args.area,
        estatus=args.estatus,
        first_name=user.nombre,
        paternal_last_name=user.apellido_paterno,
        maternal_last_name=user.apellido_materno,
        full_name=_display_name(user),
        phone=user.telefono,
        notes=args.notes,
    )
    db.add(student)
    await db.flush()
    if sede.codigo and len(sede.codigo) == 1:
        await app.generar_matricula(db, student, sede)
    else:
        _out(
            f"[aviso] La sede {sede.id} no tiene código de matrícula; "
            "el estudiante quedó sin matrícula."
        )
    await db.commit()
    _out(
        f"Perfil de estudiante creado para {user.email}: "
        f"student_id={student.id} matrícula={student.matricula or '-'}."
    )


async def cmd_student_update(db: Any, args: argparse.Namespace) -> None:
    app = _import_app()
    user = await _select_user(db, email=args.email, user_id=args.id)
    if user is None:
        raise SystemExit("Usuario no encontrado.")
    student = await _select_student(db, user.id, include_deleted=False)
    if student is None:
        raise SystemExit("El usuario no tiene perfil de estudiante activo.")

    changes: dict[str, Any] = {}
    if args.nivel is not None:
        changes["nivel"] = _normalize_nivel(args.nivel)
    if args.clear_area:
        changes["area"] = None
    elif args.area is not None:
        changes["area"] = args.area
    if args.estatus is not None:
        changes["estatus"] = args.estatus
    if args.clear_sede:
        changes["sede_id"] = None
    elif args.sede_id is not None:
        await _get_sede(db, args.sede_id)
        changes["sede_id"] = args.sede_id
    if args.clear_matricula:
        changes["matricula"] = None
    elif args.matricula is not None:
        duplicate = (
            await db.execute(
                select(app.Student).where(
                    app.Student.matricula == args.matricula,
                    app.Student.id != student.id,
                )
            )
        ).scalar_one_or_none()
        if duplicate is not None:
            raise SystemExit(f"La matrícula {args.matricula} ya está en uso.")
        changes["matricula"] = args.matricula
    if args.clear_telefono:
        changes["phone"] = None
    elif args.telefono is not None:
        changes["phone"] = args.telefono
    if args.clear_notes:
        changes["notes"] = None
    elif args.notes is not None:
        changes["notes"] = args.notes
    if args.clear_photo_url:
        changes["photo_url"] = None
    elif args.photo_url is not None:
        changes["photo_url"] = args.photo_url

    if not changes:
        raise SystemExit("Nada que actualizar.")
    if args.dry_run:
        _print_changes(changes)
        _out(f"[dry-run] Actualizaría el estudiante de {user.email}.")
        return
    for field, value in changes.items():
        setattr(student, field, value)
    await db.flush()
    await db.commit()
    _out(f"Perfil de estudiante actualizado para {user.email}.")
    _print_changes(changes)


_MENU_ACTIONS = [
    ("1", "reset-password", "Restablecer contraseña (temporal)"),
    ("2", "set-password", "Asignar nueva contraseña"),
    ("3", "activate", "Activar cuenta"),
    ("4", "deactivate", "Desactivar cuenta"),
    ("5", "set-role", "Cambiar rol"),
    ("6", "set-sede", "Cambiar sede"),
    ("7", "set-tutor", "Marcar/desmarcar como tutor"),
    ("8", "reset-2fa", "Resetear 2FA"),
    ("9", "delete", "Eliminar cuenta (soft-delete)"),
    ("10", "restore", "Restaurar cuenta eliminada"),
    ("11", "student-show", "Ver perfil de estudiante"),
]

_MENU_DISPATCH = {
    "reset-password": cmd_reset_password,
    "set-password": cmd_set_password,
    "activate": cmd_activate,
    "deactivate": cmd_deactivate,
    "set-role": cmd_set_role,
    "set-sede": cmd_set_sede,
    "set-tutor": cmd_set_tutor,
    "reset-2fa": cmd_reset_2fa,
    "delete": cmd_delete,
    "restore": cmd_restore,
    "student-show": cmd_student_show,
}


async def run_menu(db: Any) -> None:
    _out("=== Gestión de usuarios CUEP ===")
    while True:
        try:
            search = _read_input(
                "\nBuscar usuario (email/nombre, vacío=listar): "
            ).strip()
        except _InputAborted:
            _out()
            return

        rows = await _list_users(
            db, search=search or None, include_deleted=True, limit=50
        )
        await db.commit()
        _print_users_table(rows)
        if not rows:
            continue

        try:
            selection = _read_input(
                "Email o ID del usuario (vacío=salir): "
            ).strip()
        except _InputAborted:
            _out()
            return
        if not selection:
            return

        if selection.isdigit():
            user = await _select_user(
                db, user_id=int(selection), include_deleted=True
            )
        else:
            user = await _select_user(db, email=selection, include_deleted=True)
        await db.commit()
        if user is None:
            _out("Usuario no encontrado.")
            continue

        student = await _select_student(db, user.id, include_deleted=True)
        enrollment_count = 0
        if student is not None:
            app = _import_app()
            enrollment_count = int(
                (
                    await db.execute(
                        select(func.count(app.Enrollment.id)).where(
                            app.Enrollment.student_id == student.id,
                            app.Enrollment.deleted_at.is_(None),
                        )
                    )
                ).scalar()
                or 0
            )
        await db.commit()
        _out("")
        _print_user_detail(user, student, enrollment_count)
        _out("")
        for key, _, label in _MENU_ACTIONS:
            _out(f"  {key}. {label}")
        try:
            choice = _read_input("Acción: ").strip()
        except _InputAborted:
            _out()
            return
        selected = next((name for key, name, _ in _MENU_ACTIONS if key == choice), None)
        if not selected:
            _out("Opción inválida.")
            continue

        action_args = argparse.Namespace(
            email=user.email,
            id=user.id,
            dry_run=False,
            confirm=False,
            length=DEFAULT_TEMP_PASSWORD_LENGTH,
            role=None,
            sede_id=None,
            none=False,
            enabled=None,
            include_student=False,
            activate=False,
        )
        if selected == "set-role":
            try:
                action_args.role = _read_input(
                    f"Nuevo rol ({', '.join(VALID_ROLES)}): "
                ).strip()
            except _InputAborted:
                _out()
                return
        elif selected == "set-sede":
            await cmd_sedes(db, argparse.Namespace(all=False))
            try:
                value = _read_input("Nueva sede ID (vacío=sin sede): ").strip()
            except _InputAborted:
                _out()
                return
            if value:
                try:
                    action_args.sede_id = int(value)
                except ValueError:
                    _out("ID de sede inválido.")
                    continue
            else:
                action_args.none = True
        elif selected == "set-tutor":
            action_args.enabled = _interactive_confirm("¿Marcar como tutor?")
        elif selected in {"deactivate", "reset-2fa"}:
            if not _interactive_confirm(f"¿Confirmas {selected} sobre {user.email}?"):
                _out("Cancelado.")
                continue
            action_args.confirm = True
        elif selected == "delete":
            if not _interactive_confirm(
                f"¿Eliminar (soft-delete) a {user.email}?"
            ):
                _out("Cancelado.")
                continue
            action_args.confirm = f"DELETE {user.email}"

        try:
            await _MENU_DISPATCH[selected](db, action_args)
        except SystemExit as exc:
            if str(exc):
                _out(str(exc))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage_users.py",
        description="Gestión de usuarios directamente en la base de datos de CUEP.",
    )
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=None,
        help="Override de DATABASE_URL (postgresql+asyncpg://...).",
    )
    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=None,
        help="Archivo .env a cargar (default: backend/.env).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el cambio planeado sin escribir en la base de datos.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="No silenciar logging de SQL.",
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--database-url", dest="database_url", default=argparse.SUPPRESS
    )
    common.add_argument("--env-file", dest="env_file", default=argparse.SUPPRESS)
    common.add_argument(
        "--dry-run", dest="dry_run", action="store_true", default=argparse.SUPPRESS
    )
    common.add_argument(
        "--verbose", dest="verbose", action="store_true", default=argparse.SUPPRESS
    )

    sub = parser.add_subparsers(dest="command")

    def add(name: str, **kwargs: Any) -> argparse.ArgumentParser:
        return sub.add_parser(name, parents=[common], **kwargs)

    def add_target(p: argparse.ArgumentParser) -> None:
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument("--email", help="Email del usuario.")
        group.add_argument("--id", type=int, help="ID del usuario.")

    p_list = add("list", help="Listar usuarios.")
    p_list.add_argument("--search", default=None, help="Filtrar por email/nombre/teléfono.")
    p_list.add_argument("--role", default=None, help="Filtrar por rol.")
    p_list.add_argument(
        "--active-only", dest="active_only", action="store_true", help="Solo activos."
    )
    p_list.add_argument("--all", action="store_true", help="Incluir eliminados.")
    p_list.add_argument("--limit", type=int, default=100, help="Máximo de filas.")

    p_show = add("show", help="Ver detalle de un usuario.")
    add_target(p_show)
    p_show.add_argument("--all", action="store_true", help="Incluir eliminados.")

    p_sedes = add("sedes", help="Listar sedes.")
    p_sedes.add_argument("--all", action="store_true", help="Incluir eliminadas.")

    p_create = add("create", help="Crear usuario.")
    p_create.add_argument("--email", required=True)
    p_create.add_argument("--nombre", required=True)
    p_create.add_argument("--apellido-paterno", dest="apellido_paterno", required=True)
    p_create.add_argument("--apellido-materno", dest="apellido_materno", default=None)
    p_create.add_argument("--role", default="tutor")
    p_create.add_argument("--sede-id", dest="sede_id", type=int, default=None)
    p_create.add_argument("--telefono", default=None)
    p_create.add_argument("--password", default=None)
    p_create.add_argument(
        "--generate-password", dest="generate_password", action="store_true"
    )
    p_create.add_argument(
        "--es-tutor", dest="es_tutor", action=argparse.BooleanOptionalAction, default=False
    )
    p_create.add_argument(
        "--carga-max-horas", dest="carga_max_horas", type=int, default=0
    )
    p_create.add_argument("--area-principal", dest="area_principal", default=None)
    p_create.add_argument("--biografia", default=None)
    p_create.add_argument("--foto-url", dest="foto_url", default=None)

    p_create_student = add(
        "create-student", help="Crear usuario alumno con perfil de estudiante."
    )
    p_create_student.add_argument("--email", required=True)
    p_create_student.add_argument("--nombre", required=True)
    p_create_student.add_argument(
        "--apellido-paterno", dest="apellido_paterno", required=True
    )
    p_create_student.add_argument(
        "--apellido-materno", dest="apellido_materno", default=None
    )
    p_create_student.add_argument("--sede-id", dest="sede_id", type=int, required=True)
    p_create_student.add_argument("--nivel", default="PREPA")
    p_create_student.add_argument("--area", default=None)
    p_create_student.add_argument("--estatus", default="activo")
    p_create_student.add_argument("--telefono", default=None)
    p_create_student.add_argument("--notes", default=None)
    p_create_student.add_argument("--password", default=None)
    p_create_student.add_argument(
        "--generate-password", dest="generate_password", action="store_true"
    )

    p_update = add("update", help="Actualizar datos de un usuario.")
    add_target(p_update)
    p_update.add_argument("--new-email", dest="new_email", default=None, help="Nuevo email.")
    p_update.add_argument("--nombre", default=None)
    p_update.add_argument("--apellido-paterno", dest="apellido_paterno", default=None)
    p_update.add_argument("--apellido-materno", dest="apellido_materno", default=None)
    p_update.add_argument(
        "--clear-apellido-materno", dest="clear_apellido_materno", action="store_true"
    )
    p_update.add_argument("--sede-id", dest="sede_id", type=int, default=None)
    p_update.add_argument("--clear-sede", dest="clear_sede", action="store_true")
    p_update.add_argument("--role", default=None)
    p_update.add_argument(
        "--es-tutor", dest="es_tutor", action=argparse.BooleanOptionalAction, default=None
    )
    p_update.add_argument("--telefono", default=None)
    p_update.add_argument("--clear-telefono", dest="clear_telefono", action="store_true")
    p_update.add_argument("--area-principal", dest="area_principal", default=None)
    p_update.add_argument(
        "--clear-area-principal", dest="clear_area_principal", action="store_true"
    )
    p_update.add_argument(
        "--carga-max-horas", dest="carga_max_horas", type=int, default=None
    )
    p_update.add_argument("--biografia", default=None)
    p_update.add_argument(
        "--clear-biografia", dest="clear_biografia", action="store_true"
    )
    p_update.add_argument("--foto-url", dest="foto_url", default=None)
    p_update.add_argument(
        "--clear-foto-url", dest="clear_foto_url", action="store_true"
    )

    p_role = add("set-role", help="Cambiar el rol de un usuario.")
    add_target(p_role)
    p_role.add_argument("--role", required=True)

    p_sede = add("set-sede", help="Cambiar la sede de un usuario.")
    add_target(p_sede)
    sede_group = p_sede.add_mutually_exclusive_group(required=True)
    sede_group.add_argument("--sede-id", dest="sede_id", type=int)
    sede_group.add_argument("--none", action="store_true", help="Dejar sin sede.")

    p_tutor = add("set-tutor", help="Marcar o desmarcar como tutor.")
    add_target(p_tutor)
    tutor_group = p_tutor.add_mutually_exclusive_group(required=True)
    tutor_group.add_argument("--enabled", dest="enabled", action="store_true")
    tutor_group.add_argument("--disabled", dest="enabled", action="store_false")
    p_tutor.set_defaults(enabled=None)

    p_reset = add("reset-password", help="Generar contraseña temporal.")
    add_target(p_reset)
    p_reset.add_argument(
        "--length", type=int, default=DEFAULT_TEMP_PASSWORD_LENGTH
    )

    p_set = add("set-password", help="Asignar contraseña interactiva.")
    add_target(p_set)

    p_activate = add("activate", help="Activar cuenta.")
    add_target(p_activate)

    p_deactivate = add("deactivate", help="Desactivar cuenta.")
    add_target(p_deactivate)
    p_deactivate.add_argument(
        "--confirm", action="store_true", help="Requerido para desactivar."
    )

    p_delete = add("delete", help="Eliminar cuenta (soft-delete).")
    add_target(p_delete)
    p_delete.add_argument(
        "--confirm", default=None, help='Frase exacta "DELETE <email>".'
    )
    p_delete.add_argument(
        "--include-student",
        dest="include_student",
        action="store_true",
        help="También eliminar el perfil de estudiante y cancelar inscripciones.",
    )

    p_restore = add("restore", help="Restaurar cuenta eliminada.")
    add_target(p_restore)
    p_restore.add_argument(
        "--activate", action="store_true", help="Reactivar la cuenta al restaurar."
    )
    p_restore.add_argument(
        "--include-student",
        dest="include_student",
        action="store_true",
        help="También restaurar el perfil de estudiante.",
    )

    p_2fa = add("reset-2fa", help="Desactivar 2FA y borrar códigos/dispositivos.")
    add_target(p_2fa)
    p_2fa.add_argument("--confirm", action="store_true", help="Requerido para resetear.")

    p_student_show = add("student-show", help="Ver perfil de estudiante.")
    add_target(p_student_show)

    p_student_create = add(
        "student-create", help="Crear perfil de estudiante para un usuario alumno."
    )
    add_target(p_student_create)
    p_student_create.add_argument("--sede-id", dest="sede_id", type=int, required=True)
    p_student_create.add_argument("--nivel", default="PREPA")
    p_student_create.add_argument("--area", default=None)
    p_student_create.add_argument("--estatus", default="activo")
    p_student_create.add_argument("--notes", default=None)

    p_student_update = add(
        "student-update", help="Actualizar perfil de estudiante."
    )
    add_target(p_student_update)
    p_student_update.add_argument("--nivel", default=None)
    p_student_update.add_argument("--area", default=None)
    p_student_update.add_argument("--clear-area", dest="clear_area", action="store_true")
    p_student_update.add_argument("--estatus", default=None)
    p_student_update.add_argument("--sede-id", dest="sede_id", type=int, default=None)
    p_student_update.add_argument(
        "--clear-sede", dest="clear_sede", action="store_true"
    )
    p_student_update.add_argument("--matricula", default=None)
    p_student_update.add_argument(
        "--clear-matricula", dest="clear_matricula", action="store_true"
    )
    p_student_update.add_argument("--telefono", default=None)
    p_student_update.add_argument(
        "--clear-telefono", dest="clear_telefono", action="store_true"
    )
    p_student_update.add_argument("--notes", default=None)
    p_student_update.add_argument(
        "--clear-notes", dest="clear_notes", action="store_true"
    )
    p_student_update.add_argument("--photo-url", dest="photo_url", default=None)
    p_student_update.add_argument(
        "--clear-photo-url", dest="clear_photo_url", action="store_true"
    )

    add("menu", help="Menú interactivo.")

    return parser


async def _dispatch(args: argparse.Namespace) -> int:
    command = args.command
    app = _import_app()
    _print_target_banner(app.settings.DATABASE_URL)

    if command in (None, "menu"):
        async with app.async_session_factory() as db:
            await run_menu(db)
        return 0

    if args.dry_run:
        _out("[mode] DRY-RUN: no se escribirá nada.")

    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "sedes": cmd_sedes,
        "create": cmd_create,
        "create-student": cmd_create_student,
        "update": cmd_update,
        "set-role": cmd_set_role,
        "set-sede": cmd_set_sede,
        "set-tutor": cmd_set_tutor,
        "reset-password": cmd_reset_password,
        "set-password": cmd_set_password,
        "activate": cmd_activate,
        "deactivate": cmd_deactivate,
        "delete": cmd_delete,
        "restore": cmd_restore,
        "reset-2fa": cmd_reset_2fa,
        "student-show": cmd_student_show,
        "student-create": cmd_student_create,
        "student-update": cmd_student_update,
    }
    async with app.async_session_factory() as db:
        await dispatch[command](db, args)
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    global _VERBOSE
    _reconfigure_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)

    _VERBOSE = getattr(args, "verbose", False)
    _configure_output(_VERBOSE)

    env_file = getattr(args, "env_file", None)
    env_path = Path(env_file).expanduser() if env_file else DEFAULT_ENV_FILE
    if env_path.exists():
        load_dotenv(env_path, override=False)
    elif env_file:
        raise SystemExit(f"No existe el archivo de entorno: {env_path}")

    database_url = getattr(args, "database_url", None)
    if database_url:
        os.environ["DATABASE_URL"] = database_url

    try:
        return asyncio.run(_dispatch(args))
    except KeyboardInterrupt:
        _out("\nInterrumpido.")
        return 130
    except Exception as exc:
        _out(f"[error] {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
