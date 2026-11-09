import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_email_sync(to_email: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST:
        print(f"[EMAIL DEV] To={to_email} Subject={subject}\n{body}")
        return True
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] {exc}")
        return False
