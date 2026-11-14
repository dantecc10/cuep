import logging
from datetime import datetime, timezone
from string import Template

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inscripcion import ConfiguracionInscripcion
from app.models.notificacion import NotificacionOutbox, NotificacionPlantilla
from app.models.sede import Sede
from app.models.student import Student
from app.services.email import EMAIL_SENT, EMAIL_SIMULATED, send_email_sync

logger = logging.getLogger(__name__)


def student_context(
    student: Student,
    sede: Sede | None = None,
    config: ConfiguracionInscripcion | None = None,
) -> dict[str, str]:
    return {
        "nombre": student.full_name or student.first_name or "",
        "matricula": student.matricula or "",
        "sede": sede.nombre if sede else "",
        "monto": str(config.simulacro_monto) if config else "",
        "moneda": config.simulacro_moneda if config else "MXN",
    }


async def enqueue_notificacion(
    db: AsyncSession,
    clave: str,
    student: Student,
    email: str,
    context: dict | None = None,
    dedupe_key: str | None = None,
    programado_para: datetime | None = None,
) -> NotificacionOutbox | None:
    template_result = await db.execute(
        select(NotificacionPlantilla).where(
            NotificacionPlantilla.clave == clave,
            NotificacionPlantilla.activo.is_(True),
        )
    )
    template = template_result.scalar_one_or_none()
    if template is None:
        logger.warning("Plantilla de notificación no encontrada o inactiva: %s", clave)
        return None
    if dedupe_key:
        existing = await db.execute(
            select(NotificacionOutbox).where(NotificacionOutbox.dedupe_key == dedupe_key)
        )
        outbox = existing.scalar_one_or_none()
        if outbox is not None:
            return outbox

    values = {
        key: "" if value is None else str(value)
        for key, value in (context if context is not None else student_context(student)).items()
    }
    subject = Template(template.asunto).safe_substitute(values)
    body = Template(template.cuerpo_texto).safe_substitute(values)
    html = (
        Template(template.cuerpo_html).safe_substitute(values)
        if template.cuerpo_html
        else None
    )
    outbox = NotificacionOutbox(
        plantilla_id=template.id,
        plantilla_clave=template.clave,
        student_id=student.id,
        destinatario_email=email,
        asunto=subject,
        cuerpo_texto=body,
        cuerpo_html=html,
        contexto=values,
        dedupe_key=dedupe_key,
        estado="pendiente",
        programado_para=programado_para or datetime.now(timezone.utc),
    )
    db.add(outbox)
    await db.flush()
    return outbox


async def send_pending_notificaciones(
    db: AsyncSession, limit: int = 50
) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(NotificacionOutbox)
        .where(
            NotificacionOutbox.estado == "pendiente",
            NotificacionOutbox.programado_para <= now,
        )
        .order_by(NotificacionOutbox.created_at.asc())
        .limit(limit)
    )
    items = result.scalars().all()
    sent = 0
    simulated = 0
    failed = 0
    for outbox in items:
        outbox.intentos += 1
        status = await run_in_threadpool(
            send_email_sync,
            outbox.destinatario_email,
            outbox.asunto,
            outbox.cuerpo_texto,
            outbox.cuerpo_html,
        )
        if status == EMAIL_SENT:
            outbox.estado = "enviado"
            outbox.enviado_at = datetime.now(timezone.utc)
            outbox.ultimo_error = None
            sent += 1
        elif status == EMAIL_SIMULATED:
            outbox.estado = "simulado"
            outbox.enviado_at = None
            outbox.ultimo_error = (
                "Enviado en modo simulado (EMAIL_DEV_MODE); el correo no llegó al destinatario."
            )
            simulated += 1
        else:
            outbox.estado = "error"
            outbox.enviado_at = None
            outbox.ultimo_error = (
                "No se pudo enviar el correo: revisa la configuración SMTP del servidor."
            )
            failed += 1
    await db.flush()
    return {
        "procesados": len(items),
        "enviados": sent,
        "simulados": simulated,
        "fallidos": failed,
    }
