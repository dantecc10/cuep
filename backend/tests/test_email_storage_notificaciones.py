import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.database import async_session_factory
from app.models.inscripcion import EventoInscripcion
from app.models.notificacion import NotificacionOutbox, NotificacionPlantilla
from app.models.student import Student
from app.models.user import User
from app.services.email import (
    EMAIL_FAILED,
    EMAIL_SENT,
    EMAIL_SIMULATED,
    email_delivered,
    send_email_sync,
)
from app.services.notificaciones import enqueue_notificacion, send_pending_notificaciones
from app.services.storage import private_bucket, private_bucket_configured


@pytest.fixture(autouse=True)
def _sin_smtp(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr(settings, "EMAIL_DEV_MODE", False)


def test_sin_smtp_el_envio_falla(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_DEV_MODE", False)
    assert send_email_sync("a@example.com", "Asunto", "Cuerpo") == EMAIL_FAILED
    assert email_delivered(EMAIL_FAILED) is False


def test_modo_dev_marca_como_simulado(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_DEV_MODE", True)
    assert send_email_sync("a@example.com", "Asunto", "Cuerpo") == EMAIL_SIMULATED
    assert email_delivered(EMAIL_SIMULATED) is True


def test_envio_real_usa_smtp(monkeypatch):
    enviados = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            enviados["host"] = host
            enviados["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            enviados["starttls"] = True

        def login(self, user, password):
            enviados["login"] = user

        def send_message(self, message):
            enviados["to"] = message["To"]
            enviados["subject"] = message["Subject"]

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "no-reply@cuep.mx")
    monkeypatch.setattr("app.services.email.smtplib.SMTP", FakeSMTP)

    status = send_email_sync("alumno@example.com", "Hola", "Cuerpo", "<p>Cuerpo</p>")

    assert status == EMAIL_SENT
    assert enviados["to"] == "alumno@example.com"
    assert enviados["starttls"] is True


def test_bucket_privado_es_exigente(monkeypatch):
    monkeypatch.setattr(settings, "R2_PRIVATE_BUCKET", "")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "cuenta")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "R2_BUCKET", "cuep-files")

    assert private_bucket_configured() is False
    with pytest.raises(HTTPException) as exc:
        private_bucket()
    assert exc.value.status_code == 503
    assert "R2_PRIVATE_BUCKET" in exc.value.detail


def test_bucket_privado_no_cae_al_publico(monkeypatch):
    monkeypatch.setattr(settings, "R2_PRIVATE_BUCKET", "cuep-private")
    monkeypatch.setattr(settings, "R2_ACCOUNT_ID", "cuenta")
    monkeypatch.setattr(settings, "R2_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(settings, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(settings, "R2_BUCKET", "cuep-files")

    assert private_bucket_configured() is True
    assert private_bucket() == "cuep-private"


async def _crear_alumno() -> tuple[int, str]:
    unique = uuid.uuid4().hex[:10]
    async with async_session_factory() as db:
        user = User(
            email=f"notif-{unique}@example.com",
            password_hash="x",
            nombre="Alumno",
            apellido_paterno="Prueba",
            role="alumno",
            es_tutor=False,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        student = Student(
            user_id=user.id,
            email=user.email,
            nivel="PREPA",
            estatus="registrado",
            anio=2026,
        )
        db.add(student)
        await db.flush()
        await db.commit()
        return student.id, user.email


@pytest.mark.asyncio
async def test_outbox_queda_en_error_sin_smtp(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_DEV_MODE", False)
    student_id, email = await _crear_alumno()
    async with async_session_factory() as db:
        outbox = NotificacionOutbox(
            destinatario_email=email,
            asunto="Prueba",
            cuerpo_texto="Cuerpo",
            estado="pendiente",
            programado_para=datetime.now(timezone.utc),
        )
        db.add(outbox)
        await db.flush()
        await db.commit()
        outbox_id = outbox.id

    async with async_session_factory() as db:
        resultado = await send_pending_notificaciones(db, limit=50)
        await db.commit()
        assert resultado["fallidos"] >= 1
        assert resultado["enviados"] == 0
        assert resultado["simulados"] == 0
        row = await db.get(NotificacionOutbox, outbox_id)
        assert row.estado == "error"
        assert "SMTP" in row.ultimo_error


@pytest.mark.asyncio
async def test_outbox_marca_simulado_en_modo_dev(monkeypatch):
    monkeypatch.setattr(settings, "EMAIL_DEV_MODE", True)
    student_id, email = await _crear_alumno()
    async with async_session_factory() as db:
        outbox = NotificacionOutbox(
            destinatario_email=email,
            asunto="Prueba",
            cuerpo_texto="Cuerpo",
            estado="pendiente",
            programado_para=datetime.now(timezone.utc),
        )
        db.add(outbox)
        await db.flush()
        await db.commit()
        outbox_id = outbox.id

    async with async_session_factory() as db:
        resultado = await send_pending_notificaciones(db, limit=50)
        await db.commit()
        assert resultado["simulados"] >= 1
        assert resultado["enviados"] == 0
        row = await db.get(NotificacionOutbox, outbox_id)
        assert row.estado == "simulado"
        assert row.enviado_at is None


@pytest.mark.asyncio
async def test_html_de_plantilla_se_sustituye():
    student_id, email = await _crear_alumno()
    clave = f"prueba_html_{uuid.uuid4().hex[:6]}"
    async with async_session_factory() as db:
        db.add(
            NotificacionPlantilla(
                clave=clave,
                nombre="Prueba HTML",
                asunto="Hola $nombre",
                cuerpo_texto="Hola $nombre",
                cuerpo_html="<p>Hola $nombre, tu matrícula es $matricula</p>",
                activo=True,
            )
        )
        await db.commit()
        student = await db.get(Student, student_id)
        student.full_name = "Ana Pérez"
        student.matricula = f"CL{uuid.uuid4().hex[:6].upper()}"
        await db.commit()

    async with async_session_factory() as db:
        student = await db.get(Student, student_id)
        outbox = await enqueue_notificacion(db, clave, student, email)
        await db.commit()
        assert outbox is not None
        assert outbox.asunto == "Hola Ana Pérez"
        assert outbox.cuerpo_html.startswith("<p>Hola Ana Pérez, tu matrícula es CL")


@pytest.mark.asyncio
async def test_dedupe_no_duplica_notificaciones():
    student_id, email = await _crear_alumno()
    clave = f"prueba_dedupe_{uuid.uuid4().hex[:6]}"
    async with async_session_factory() as db:
        db.add(
            NotificacionPlantilla(
                clave=clave,
                nombre="Prueba dedupe",
                asunto="Hola",
                cuerpo_texto="Hola",
                activo=True,
            )
        )
        await db.commit()

    async with async_session_factory() as db:
        student = await db.get(Student, student_id)
        primero = await enqueue_notificacion(
            db, clave, student, email, dedupe_key=f"dedupe-{clave}"
        )
        await db.commit()
        segundo = await enqueue_notificacion(
            db, clave, student, email, dedupe_key=f"dedupe-{clave}"
        )
        await db.commit()
        assert primero is not None
        assert segundo is not None
        assert primero.id == segundo.id


def test_eventos_de_inscripcion_siguen_disponibles():
    assert EventoInscripcion.__tablename__ == "eventos_inscripcion"
