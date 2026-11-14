#!/usr/bin/env python3
"""Reporte de estado de los módulos del CUEP.

Se ejecuta al final de `scripts/deploy.sh` (y también se puede correr solo)
para saber, después de un despliegue:

- qué variables de entorno están correctas, cuáles faltan y cuáles siguen con
  el valor de ejemplo;
- qué módulos quedan funcionables, con limitaciones o sin configurar;
- qué datos hay ahora mismo en la base (padrón, cargos, pagos, avisos);
- qué pasos concretos hay que seguir.

No modifica nada: sólo lee `.env`, la base de datos y el bucket de R2.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections import Counter
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
GREY = "\033[90m"

OK = 0
AVISO = 1
FALLA = 2

_cuentas = Counter()


def _color_enabled() -> bool:
    return sys.stdout.isatty()


def _c(color: str, text: str) -> str:
    if not _color_enabled():
        return text
    return f"{color}{text}{RESET}"


def registrar(nivel: int, modulo: str, mensaje: str = "", detalle: str = "") -> None:
    _cuentas[nivel] += 1
    if nivel == OK:
        etiqueta = _c(f"{GREEN}  OK    {RESET}", "  OK    ")
    elif nivel == AVISO:
        etiqueta = _c(f"{YELLOW} AVISO {RESET}", " AVISO ")
    else:
        etiqueta = _c(f"{RED} FALLA {RESET}", " FALLA ")
    texto = modulo
    if mensaje:
        texto = f"{modulo}: {mensaje}"
    print(f"{etiqueta} {texto}")
    if detalle:
        print(f"         {_c(GREY, detalle)}{RESET}" if _color_enabled() else f"         {detalle}")


def seccion(titulo: str) -> None:
    print()
    print(_c(f"{BOLD}{BLUE}▸ {titulo}{RESET}", f"▸ {titulo}"))


def nota(mensaje: str) -> None:
    print(f"  {_c(CYAN, '·')}{RESET} {mensaje}")


# --------------------------------------------------------------------------
# Variables de entorno
# --------------------------------------------------------------------------

# (variable, módulo, criticidad, valores de ejemplo que hay que cambiar)
VARIABLES = (
    ("DATABASE_URL", "Base de datos", "requerido", ("CAMBIAR",)),
    ("JWT_SECRET", "Autenticación", "requerido", ("change-this-to-a-random-secret-at-least-32-chars",)),
    ("PUBLIC_APP_URL", "Pase y QR", "requerido", ("http://localhost:3000",)),
    ("CORS_ORIGINS", "Frontend", "requerido", ()),
    ("R2_ACCOUNT_ID", "Fotos de perfil", "requerido", ()),
    ("R2_ACCESS_KEY_ID", "Fotos de perfil", "requerido", ()),
    ("R2_SECRET_ACCESS_KEY", "Fotos de perfil", "requerido", ()),
    ("R2_BUCKET", "Fotos de perfil", "requerido", ()),
    ("R2_PUBLIC_BASE", "Fotos de perfil", "opcional", ()),
    ("R2_PRIVATE_BUCKET", "Comprobantes de pago", "requerido", ()),
    ("PAYMENT_PROOF_MAX_BYTES", "Comprobantes de pago", "opcional", ()),
    ("SMTP_HOST", "Correo y 2FA", "requerido", ()),
    ("SMTP_PORT", "Correo y 2FA", "opcional", ()),
    ("SMTP_USER", "Correo y 2FA", "opcional", ()),
    ("SMTP_PASSWORD", "Correo y 2FA", "opcional", ()),
    ("SMTP_FROM_EMAIL", "Correo y 2FA", "recomendado", ()),
    ("SMTP_FROM_NAME", "Correo y 2FA", "opcional", ()),
    ("EMAIL_DEV_MODE", "Correo y 2FA", "opcional", ()),
    ("WORKER_API_KEY", "Worker y cola de avisos", "requerido", ("change-this-worker-key",)),
    ("TOTP_ENCRYPTION_KEY", "2FA", "recomendado", ()),
    ("COOKIE_SECURE", "Cookies de sesión", "recomendado", ()),
    ("COOKIE_SAMESITE", "Cookies de sesión", "opcional", ()),
    ("COOKIE_DOMAIN", "Cookies de sesión", "opcional", ()),
    ("REFRESH_COOKIE_NAME", "Cookies de sesión", "opcional", ()),
    ("REFRESH_COOKIE_PATH", "Cookies de sesión", "opcional", ()),
    ("APP_TIMEZONE", "General", "opcional", ()),
    ("ENVIRONMENT", "General", "opcional", ()),
    ("SOLVER_TIMEOUT", "Motor de horarios", "opcional", ()),
)


def leer_env() -> dict[str, str]:
    try:
        from dotenv import dotenv_values

        valores = dotenv_values(BACKEND_DIR / ".env")
    except Exception:
        return {}
    return {clave: (valor or "") for clave, valor in valores.items()}


def revisar_variables(env: dict[str, str]) -> None:
    seccion("Variables de entorno (backend/.env)")
    if not env:
        registrar(
            FALLA,
            "backend/.env",
            "No se encontró o no se pudo leer. Copia backend/.env.example y ajústalo.",
        )
        return

    entorno = env.get("ENVIRONMENT", "").strip().lower()
    produccion = entorno == "production"
    desarrollo = entorno in {"", "development", "dev", "local"}
    criticas = {"DATABASE_URL", "JWT_SECRET"}

    opcionales: dict[str, list[str]] = {}

    for nombre, modulo, criticidad, ejemplos in VARIABLES:
        valor = env.get(nombre, "")
        if valor.strip() == "":
            if criticidad == "opcional":
                opcionales.setdefault(modulo, []).append(nombre)
                continue
            if criticidad == "requerido" and (not desarrollo or nombre in criticas):
                registrar(
                    FALLA,
                    f"{nombre} ({modulo})",
                    "Falta. Ese módulo no va a funcionar hasta que lo definas.",
                )
            else:
                registrar(
                    AVISO,
                    f"{nombre} ({modulo})",
                    "Sin valor: se usará el valor por defecto de la app.",
                )
            continue
        if valor.strip() in ejemplos:
            registrar(
                AVISO,
                f"{nombre} ({modulo})",
                f"Conserva el valor de ejemplo ({valor.strip()}).",
            )
            continue
        registrar(OK, f"{nombre} ({modulo})", "Configurado.")

    for modulo, nombres in opcionales.items():
        registrar(
            AVISO,
            f"{modulo} (opcionales)",
            "sin valor: " + ", ".join(nombres) + " (se usará el valor por defecto).",
        )

    if env.get("EMAIL_DEV_MODE", "").strip().lower() in {"1", "true", "yes", "si"}:
        registrar(
            AVISO,
            "Correo simulado (EMAIL_DEV_MODE)",
            "Los correos no se envían: se imprimen en el log y quedan como 'simulado'. "
            "Apágalo en el servidor.",
        )
    if produccion and env.get("COOKIE_SECURE", "").strip().lower() in {"", "false", "0", "no"}:
        registrar(
            AVISO,
            "Cookies de sesión (COOKIE_SECURE)",
            "En producción debería ser True para viajar por HTTPS.",
        )
    if produccion and env.get("PUBLIC_APP_URL", "").startswith("http://localhost"):
        registrar(
            AVISO,
            "Pase y QR (PUBLIC_APP_URL)",
            "Apunta a localhost: los QR y los pases se abrirán en el equipo equivocado.",
        )
    return


# --------------------------------------------------------------------------
# Migraciones
# --------------------------------------------------------------------------


def revision_actual() -> str | None:
    directorio = BACKEND_DIR / "alembic" / "versions"
    revisiones: dict[str, str | None] = {}
    for archivo in directorio.glob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        revision = re.search(r'^revision:\s*str\s*=\s*"([^"]+)"', texto, re.M)
        anterior = re.search(r'^down_revision[^=]*=\s*(?:Union\[str, None\]\s*=\s*)?"([^"]*)"', texto, re.M)
        if revision:
            revisiones[revision.group(1)] = anterior.group(1) if anterior else None
    if not revisiones:
        return None
    referenciadas = {valor for valor in revisiones.values() if valor}
    candidatos = [clave for clave in revisiones if clave not in referenciadas]
    return candidatos[0] if candidatos else None


def comprobar_migraciones(esperada: str | None) -> None:
    seccion("Migraciones")
    cabecera = revision_actual()
    if cabecera is None:
        registrar(AVISO, "Alembic", "No se pudo leer el historial de revisiones.")
        return
    if esperada and cabecera != esperada:
        registrar(
            FALLA,
            "Alembic",
            f"La revisión del código es {cabecera} y esperabas {esperada}. "
            "Revisa que el servidor esté en la misma versión.",
        )
        return
    registrar(OK, "Alembic", f"Revisión más reciente: {cabecera}.")


# --------------------------------------------------------------------------
# Base de datos y módulos
# --------------------------------------------------------------------------


async def revisar_base(env: dict[str, str]) -> None:
    seccion("Base de datos y datos del ciclo")
    entorno = env.get("ENVIRONMENT", "").strip().lower()
    desarrollo = entorno in {"", "development", "dev", "local"}
    from sqlalchemy import func, select, text

    from app.core.database import async_session_factory
    from app.models.inscripcion import ConfiguracionInscripcion
    from app.models.notificacion import NotificacionOutbox
    from app.models.pago import Cargo, Pago
    from app.models.sede import Sede
    from app.models.student import Student

    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
            registrar(OK, "Conexión a PostgreSQL", "La base responde.")

            try:
                aplicada = (
                    await db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                ).scalar_one_or_none()
            except Exception:  # noqa: BLE001
                aplicada = None
            codigo = revision_actual()
            if aplicada and codigo and aplicada != codigo:
                registrar(
                    FALLA,
                    "Migraciones aplicadas",
                    f"La base está en {aplicada} y el código en {codigo}. "
                    "Ejecuta `alembic upgrade head` en el servidor.",
                )
            elif aplicada:
                registrar(OK, "Migraciones aplicadas", f"La base está en {aplicada}.")

            try:
                config = (
                    await db.execute(
                        select(ConfiguracionInscripcion).where(
                            ConfiguracionInscripcion.id == 1
                        )
                    )
                ).scalar_one_or_none()
            except Exception as exc:  # noqa: BLE001
                registrar(FALLA, "Configuración del ciclo", f"No se pudo leer: {exc}")
                return
            if config is None:
                registrar(
                    AVISO,
                    "Configuración del ciclo",
                    "Todavía no existe: se creará con el año actual al primer registro.",
                )
                return

            registrar(
                OK,
                "Configuración del ciclo",
                f"año {config.anio} · registro "
                f"{'abierto' if config.registro_abierto else 'cerrado'} · simulacro "
                f"{'activo' if config.simulacro_activo else 'inactivo'} "
                f"({config.simulacro_monto} {config.simulacro_moneda}) · efectivo "
                f"{'habilitado' if config.pago_efectivo_habilitado else 'deshabilitado'} · "
                f"transferencias "
                f"{'habilitadas' if config.transferencia_habilitada else 'deshabilitadas'}",
            )

            try:
                estudiantes = (
                    await db.execute(
                        select(Student.estatus, func.count(Student.id))
                        .where(Student.anio == config.anio, Student.deleted_at.is_(None))
                        .group_by(Student.estatus)
                    )
                ).all()
            except Exception:  # noqa: BLE001
                estudiantes = []
            if estudiantes:
                detalle = ", ".join(
                    f"{estado}: {total}" for estado, total in sorted(estudiantes)
                )
                registrar(OK, f"Padrón {config.anio}", detalle)
            else:
                registrar(
                    AVISO,
                    f"Padrón {config.anio}",
                    "No hay aspirantes registrados todavía en el año activo.",
                )

            try:
                cargos = (
                    await db.execute(
                        select(Cargo.estado, func.count(Cargo.id))
                        .where(Cargo.anio == config.anio, Cargo.deleted_at.is_(None))
                        .group_by(Cargo.estado)
                    )
                ).all()
                pagos = (
                    await db.execute(
                        select(Pago.estado, func.count(Pago.id))
                        .where(Pago.deleted_at.is_(None))
                        .group_by(Pago.estado)
                    )
                ).all()
                avisos = (
                    await db.execute(
                        select(NotificacionOutbox.estado, func.count(NotificacionOutbox.id))
                        .group_by(NotificacionOutbox.estado)
                    )
                ).all()
            except Exception as exc:  # noqa: BLE001
                registrar(AVISO, "Cargos, pagos y avisos", f"No se pudieron contar: {exc}")
                return

            if cargos:
                registrar(
                    OK,
                    "Cargos del ciclo",
                    ", ".join(f"{estado}: {total}" for estado, total in sorted(cargos)),
                )
            if pagos:
                pendientes = dict(pagos).get("pendiente", 0)
                registrar(
                    AVISO if pendientes else OK,
                    "Pagos",
                    ", ".join(f"{estado}: {total}" for estado, total in sorted(pagos))
                    + (" (hay transferencias por validar)" if pendientes else ""),
                )
            if avisos:
                detalle = ", ".join(
                    f"{estado}: {total}" for estado, total in sorted(avisos)
                )
                errores = dict(avisos).get("error", 0)
                registrar(
                    AVISO if errores else OK,
                    "Cola de notificaciones",
                    detalle + (" (revisa los errores)" if errores else ""),
                )

            try:
                sedes = (await db.execute(select(Sede))).scalars().all()
            except Exception:  # noqa: BLE001
                sedes = []
            activas = [sede for sede in sedes if sede.activo and sede.deleted_at is None]
            sin_codigo = [sede.nombre for sede in activas if not sede.codigo]
            if sin_codigo:
                registrar(
                    AVISO,
                    "Sedes",
                    f"{len(activas)} activas; sin código de matrícula (no podrán matricular): "
                    + ", ".join(sin_codigo[:5])
                    + ("…" if len(sin_codigo) > 5 else ""),
                )
            elif activas:
                registrar(OK, "Sedes", f"{len(activas)} activas y todas con código de matrícula.")

            _modulos(config, env, activas, sin_codigo, desarrollo)
    except Exception as exc:  # noqa: BLE001
        registrar(
            FALLA,
            "Conexión a PostgreSQL",
            f"No se pudo completar la revisión: {exc}",
        )


def revisar_r2(env: dict[str, str], probe: bool = False) -> None:
    seccion("Almacenamiento (Cloudflare R2)")
    credenciales = all(
        env.get(clave, "").strip()
        for clave in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    )
    if not credenciales:
        registrar(
            AVISO,
            "Cloudflare R2",
            "Sin credenciales: las fotos de perfil y los comprobantes no se pueden subir.",
        )
        return
    try:
        import boto3
    except ImportError:
        registrar(AVISO, "Cloudflare R2", "boto3 no está instalado; no se pudo comprobar.")
        return

    cliente = boto3.client(
        "s3",
        endpoint_url=f"https://{env.get('R2_ACCOUNT_ID', '')}.r2.cloudflarestorage.com",
        aws_access_key_id=env.get("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=env.get("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

    publico = env.get("R2_BUCKET", "").strip()
    if publico:
        try:
            cliente.head_bucket(Bucket=publico)
            registrar(OK, "Bucket público (fotos)", f"{publico} responde correctamente.")
        except Exception as exc:  # noqa: BLE001
            registrar(
                AVISO,
                "Bucket público (fotos)",
                f"No se pudo comprobar {publico}: {type(exc).__name__}",
            )
    else:
        registrar(AVISO, "Bucket público (fotos)", "Falta R2_BUCKET.")

    privado = env.get("R2_PRIVATE_BUCKET", "").strip()
    if not privado:
        registrar(
            FALLA,
            "Bucket privado (comprobantes)",
            "Falta R2_PRIVATE_BUCKET: la subida de comprobantes de transferencia "
            "responderá 503 y las transferencias no podrán validarse con imagen.",
        )
        return
    if privado == publico:
        registrar(
            FALLA,
            "Bucket privado (comprobantes)",
            "R2_PRIVATE_BUCKET es igual a R2_BUCKET: los comprobantes caerían en el "
            "bucket público. Crea un bucket aparte.",
        )
        return
    try:
        cliente.head_bucket(Bucket=privado)
        registrar(OK, "Bucket privado (comprobantes)", f"{privado} responde correctamente.")
    except Exception as exc:  # noqa: BLE001
        registrar(
            AVISO,
            "Bucket privado (comprobantes)",
            f"No se pudo comprobar {privado}: {type(exc).__name__}. Revisa el token y sus permisos.",
        )
        return

    if probe:
        clave = "diagnostico/prueba-cuep.txt"
        try:
            cliente.put_object(
                Bucket=privado, Key=clave, Body=b"prueba CUEP", ContentType="text/plain"
            )
            cliente.get_object(Bucket=privado, Key=clave)["Body"].read()
            cliente.delete_object(Bucket=privado, Key=clave)
            registrar(
                OK,
                "Prueba de escritura (bucket privado)",
                "subió, leyó y borró un archivo de prueba: el token tiene permisos.",
            )
        except Exception as exc:  # noqa: BLE001
            registrar(
                FALLA,
                "Prueba de escritura (bucket privado)",
                f"No se pudo escribir en {privado}: {type(exc).__name__}: {exc}",
            )


# --------------------------------------------------------------------------
# Resumen
# --------------------------------------------------------------------------


def resumen() -> int:
    seccion("Resumen")
    print(
        "  "
        + _c(GREEN, f"{_cuentas[OK]} correctos")
        + " · "
        + _c(YELLOW, f"{_cuentas[AVISO]} advertencias")
        + " · "
        + _c(RED, f"{_cuentas[FALLA]} errores")
    )

    if _cuentas[FALLA]:
        print()
        print(_c(f"{BOLD}{RED}Hay puntos que resolver antes de anunciar el despliegue:{RESET}", "Hay puntos que resolver antes de anunciar el despliegue:"))
        print("  - Los módulos marcados en rojo no funcionan hasta que los configures.")
        print("  - Revisa backend/.env contra backend/.env.example y vuelve a ejecutar")
        print("    python scripts/deploy_report.py para confirmar.")
        return 1
    if _cuentas[AVISO]:
        print()
        print(_c(f"{BOLD}{YELLOW}Todo funciona; quedan advertencias:{RESET}", "Todo funciona; quedan advertencias:"))
        print("  - Son ajustes recomendados, no bloqueos del despliegue.")
    else:
        print()
        print(_c(f"{GREEN}Despliegue completo y módulos correctamente configurados.{RESET}", ""))
    return 0


def _modulos(
    config,
    env: dict[str, str],
    sedes_activas: list,
    sedes_sin_codigo: list,
    desarrollo: bool,
) -> None:
    """Resumen por funcionalidad: qué quedó operante y qué no."""
    seccion("Módulos y funcionalidades")

    def nivel(ok: bool, modulo: str, mensaje: str) -> None:
        if ok:
            registrar(OK, modulo, mensaje)
        else:
            registrar(AVISO if desarrollo else FALLA, modulo, mensaje)

    nivel(
        bool(config.registro_abierto),
        "Registro de aspirantes",
        "abierto" if config.registro_abierto else "cerrado (se abre desde la configuración)",
    )
    nivel(
        not sedes_sin_codigo,
        "Matrícula y pase",
        (
            f"{len(sedes_activas)} sedes con código: se puede matricular"
            if not sedes_sin_codigo
            else f"{len(sedes_sin_codigo)} sedes sin código: no podrán matricular"
        ),
    )
    registrar(
        OK,
        "Mesa de inscripción",
        "check-in por matrícula, QR, correo o teléfono",
    )
    nivel(
        bool(config.simulacro_activo),
        "Simulacro",
        (
            f"activo ({config.simulacro_monto} {config.simulacro_moneda})"
            if config.simulacro_activo
            else "inactivo: no se ofrece a los aspirantes"
        ),
    )
    nivel(
        bool(config.pago_efectivo_habilitado),
        "Cobro en efectivo",
        (
            "habilitado en sede"
            if config.pago_efectivo_habilitado
            else "deshabilitado: la mesa no puede cobrar"
        ),
    )

    bucket = env.get("R2_PRIVATE_BUCKET", "").strip()
    credenciales_r2 = all(
        env.get(clave, "").strip()
        for clave in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
    )
    if config.transferencia_habilitada and bucket and credenciales_r2:
        registrar(OK, "Transferencias", "habilitadas y con bucket privado configurado")
    elif config.transferencia_habilitada and not bucket:
        nivel(
            False,
            "Transferencias",
            "habilitadas pero sin R2_PRIVATE_BUCKET: los comprobantes no se podrán subir",
        )
    else:
        registrar(AVISO, "Transferencias", "deshabilitadas en la configuración del ciclo")

    if bucket and credenciales_r2:
        registrar(OK, "Comprobantes de pago", f"bucket privado {bucket}")
    else:
        nivel(
            False,
            "Comprobantes de pago",
            "sin bucket privado: la subida responderá 503",
        )

    if env.get("SMTP_HOST", "").strip():
        registrar(OK, "Correo (SMTP)", f"envía desde {env['SMTP_HOST'].strip()}")
    else:
        nivel(
            False,
            "Correo (SMTP)",
            "sin SMTP: los avisos y el 2FA no se entregarán",
        )

    if env.get("TOTP_ENCRYPTION_KEY", "").strip():
        registrar(OK, "2FA", "clave de cifrado configurada")
    else:
        registrar(AVISO, "2FA", "sin TOTP_ENCRYPTION_KEY: no se pueden cifrar los secretos")

    registrar(
        OK,
        "Worker de horarios",
        "se ejecuta en el equipo del coordinador (opcional en el servidor)",
    )


async def _cerrar_pool() -> None:
    try:
        from app.core.database import engine

        pendientes = engine.pool.checkedout() if hasattr(engine.pool, "checkedout") else -1
        if pendientes:
            print(_c(GREY, f"  (conexiones sin devolver: {pendientes})"))
        await engine.dispose()
    except Exception as exc:  # noqa: BLE001
        print(_c(GREY, f"  (no se pudo cerrar el pool: {exc})"))


async def main() -> int:
    parser = argparse.ArgumentParser(description="Reporte de estado de los módulos del CUEP.")
    parser.add_argument(
        "--head",
        help="Revisión de Alembic esperada (la que trae el código desplegado).",
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Prueba de escritura: sube, lee y borra un archivo en el bucket privado.",
    )
    args = parser.parse_args()

    print(_c(f"{BOLD}Reporte de estado del CUEP{RESET}", "Reporte de estado del CUEP"))
    print(_c(GREY, f"proyecto: {ROOT_DIR}"))

    env = leer_env()
    try:
        revisar_variables(env)
        comprobar_migraciones(args.head)
        await revisar_base(env)
        revisar_r2(env, probe=args.probe)
    finally:
        await _cerrar_pool()
    return resumen()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
