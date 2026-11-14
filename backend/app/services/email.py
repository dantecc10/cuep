import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)

EMAIL_SENT = "sent"
EMAIL_SIMULATED = "simulated"
EMAIL_FAILED = "failed"


def smtp_configured() -> bool:
    return bool(settings.SMTP_HOST)


def send_email_sync(
    to_email: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> str:
    """Envía un correo y devuelve EMAIL_SENT, EMAIL_SIMULATED o EMAIL_FAILED.

    El envío es real en todos los entornos: si no hay SMTP configurado la
    función falla (y el outbox lo registra como error) salvo que se habilite
    explícitamente EMAIL_DEV_MODE, en cuyo caso el mensaje sólo se imprime en
    la consola y queda marcado como simulado.
    """
    if not smtp_configured():
        if settings.EMAIL_DEV_MODE:
            print(f"[EMAIL DEV] To={to_email} Subject={subject}\n{body}")
            return EMAIL_SIMULATED
        logger.error(
            "SMTP no configurado; no se pudo enviar el correo a %s (asunto: %s)",
            to_email,
            subject,
        )
        return EMAIL_FAILED

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return EMAIL_SENT
    except Exception as exc:
        logger.error("Falló el envío de correo a %s: %s", to_email, exc)
        return EMAIL_FAILED


def email_delivered(status: str) -> bool:
    return status in {EMAIL_SENT, EMAIL_SIMULATED}
