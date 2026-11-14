import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.main import app
from app.models.inscripcion import EventoInscripcion
from app.models.materia import Materia
from app.models.notificacion import NotificacionOutbox
from app.models.sede import Grupo, Sede
from app.models.student import Enrollment, Student
from app.models.user import User


async def _crear_escenario(capacidad: int = 2):
    unique = uuid.uuid4().hex[:8]
    async with async_session_factory() as db:
        sede = Sede(nombre=f"Sede prueba {unique}", ciudad="Puebla", codigo=None)
        otra = Sede(nombre=f"Otra sede {unique}", ciudad="Puebla", codigo=None)
        db.add_all([sede, otra])
        await db.flush()
        materia = Materia(nombre=f"Materia {unique}", nivel="PREPA", area="Exactas")
        db.add(materia)
        await db.flush()
        grupo = Grupo(
            sede_id=sede.id,
            materia_id=materia.id,
            nombre=f"Grupo {unique}",
            horas_totales=4,
            bloque_horas=2,
            capacidad=capacidad,
        )
        db.add(grupo)
        await db.flush()

        admin = User(
            email=f"admin-grupos-{unique}@example.com",
            password_hash=get_password_hash("admin123"),
            nombre="Admin",
            apellido_paterno="Prueba",
            role="admin",
            es_tutor=False,
            is_active=True,
        )
        sede_admin = User(
            email=f"sede-grupos-{unique}@example.com",
            password_hash=get_password_hash("admin123"),
            nombre="Sede",
            apellido_paterno="Prueba",
            role="inscripcion",
            es_tutor=False,
            is_active=True,
            sede_id=sede.id,
        )
        otra_admin = User(
            email=f"otra-grupos-{unique}@example.com",
            password_hash=get_password_hash("admin123"),
            nombre="Otra",
            apellido_paterno="Prueba",
            role="inscripcion",
            es_tutor=False,
            is_active=True,
            sede_id=otra.id,
        )
        db.add_all([admin, sede_admin, otra_admin])
        await db.flush()

        student = Student(
            user_id=None,
            email=f"alumno-grupos-{unique}@example.com",
            sede_id=sede.id,
            nivel="PREPA",
            area=None,
            estatus="en_inscripcion",
            anio=2026,
        )
        db.add(student)
        await db.flush()
        await db.commit()
        return {
            "sede_id": sede.id,
            "otra_sede_id": otra.id,
            "grupo_id": grupo.id,
            "materia_id": materia.id,
            "student_id": student.id,
            "admin": admin.email,
            "sede_admin": sede_admin.email,
            "otra_admin": otra_admin.email,
        }


async def _token(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "admin123"}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_asigna_grupo_y_deja_evento():
    data = await _crear_escenario()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {await _token(client, data['admin'])}"}
        response = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=headers,
            json={"grupo_id": data["grupo_id"]},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["estado"] == "confirmada"
        assert body["grupo_id"] == data["grupo_id"]
        assert body["payment_status"] == "no_requerido"

        listado = await client.get(
            f"/api/v1/inscripciones/{data['student_id']}/grupos", headers=headers
        )
        assert listado.status_code == 200
        assert len(listado.json()) == 1

    async with async_session_factory() as db:
        eventos = (
            await db.execute(
                select_eventos(data["student_id"])
            )
        ).scalars().all()
        assert [evento.tipo for evento in eventos] == ["asignacion_grupo"]
        assert eventos[0].detalle["grupo_id"] == data["grupo_id"]

        outbox = (
            await db.execute(
                select_outbox(data["student_id"])
            )
        ).scalars().all()
        assert len(outbox) == 1
        assert outbox[0].plantilla_clave == "grupo_asignado"
        assert outbox[0].estado == "pendiente"


@pytest.mark.asyncio
async def test_no_permite_duplicar_grupo():
    data = await _crear_escenario()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {await _token(client, data['admin'])}"}
        first = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=headers,
            json={"grupo_id": data["grupo_id"]},
        )
        assert first.status_code == 201
        second = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=headers,
            json={"grupo_id": data["grupo_id"]},
        )
        assert second.status_code == 409
        assert "ya está en este grupo" in second.json()["detail"]


@pytest.mark.asyncio
async def test_grupo_lleno_manda_a_lista_de_espera():
    data = await _crear_escenario(capacidad=0)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {await _token(client, data['admin'])}"}
        response = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=headers,
            json={"grupo_id": data["grupo_id"]},
        )
        assert response.status_code == 201, response.text
        assert response.json()["estado"] == "lista_espera"


@pytest.mark.asyncio
async def test_rol_inscripcion_opera_su_sede_y_no_otra():
    data = await _crear_escenario()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers_sede = {"Authorization": f"Bearer {await _token(client, data['sede_admin'])}"}
        headers_otra = {"Authorization": f"Bearer {await _token(client, data['otra_admin'])}"}

        permitido = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=headers_sede,
            json={"grupo_id": data["grupo_id"]},
        )
        assert permitido.status_code == 201

        ajeno = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=headers_otra,
            json={"grupo_id": data["grupo_id"]},
        )
        assert ajeno.status_code == 403


@pytest.mark.asyncio
async def test_alumno_no_puede_asignar_grupos():
    data = await _crear_escenario()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_headers = {"Authorization": f"Bearer {await _token(client, data['admin'])}"}
        asignacion = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=admin_headers,
            json={"grupo_id": data["grupo_id"]},
        )
        assert asignacion.status_code == 201
        enrollment_id = asignacion.json()["enrollment_id"]

        response = await client.delete(
            f"/api/v1/inscripciones/{data['student_id']}/grupos/{enrollment_id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["desasignado"] == enrollment_id

    async with async_session_factory() as db:
        enrollment = await db.get(Enrollment, enrollment_id)
        assert enrollment.estado == "cancelada"
        assert enrollment.deleted_at is not None
        eventos = (await db.execute(select_eventos(data["student_id"]))).scalars().all()
        assert any(evento.estado_nuevo == "cancelada" for evento in eventos)


@pytest.mark.asyncio
async def test_grupo_de_otra_sede_se_rechaza():
    data = await _crear_escenario()
    async with async_session_factory() as db:
        materia = await db.get(Materia, data["materia_id"])
        grupo = Grupo(
            sede_id=data["otra_sede_id"],
            materia_id=materia.id,
            nombre="Grupo ajeno",
            horas_totales=4,
            bloque_horas=2,
            capacidad=5,
        )
        db.add(grupo)
        await db.flush()
        await db.commit()
        grupo_id = grupo.id

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {await _token(client, data['admin'])}"}
        response = await client.post(
            f"/api/v1/inscripciones/{data['student_id']}/grupos",
            headers=headers,
            json={"grupo_id": grupo_id},
        )
        assert response.status_code == 400
        assert "sede" in response.json()["detail"]


def select_eventos(student_id: int):
    from sqlalchemy import select

    return select(EventoInscripcion).where(EventoInscripcion.student_id == student_id)


def select_outbox(student_id: int):
    from sqlalchemy import select

    return select(NotificacionOutbox).where(NotificacionOutbox.student_id == student_id)
