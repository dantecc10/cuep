import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import get_password_hash
from app.main import app
from app.models.inscripcion import EventoInscripcion
from app.models.sede import Sede
from app.models.student import Student
from app.models.user import User


async def _sede_de_pruebas(codigo: str, con_codigo: bool = True) -> int:
    """Devuelve (o crea) una sede estable para las pruebas del módulo."""
    async with async_session_factory() as db:
        sede = (
            await db.execute(select(Sede).where(Sede.codigo == codigo))
        ).scalar_one_or_none()
        if sede is None:
            sede = Sede(
                nombre=f"Sede pruebas {codigo}",
                ciudad="Puebla",
                codigo=codigo if con_codigo else None,
            )
            db.add(sede)
            await db.flush()
            await db.commit()
        return sede.id


async def _crear_sede(con_codigo: bool = True) -> int:
    """Sede sin código: no consume los códigos de un carácter del catálogo."""
    unique = uuid.uuid4().hex[:6]
    async with async_session_factory() as db:
        sede = Sede(
            nombre=f"Sede inscripción {unique}",
            ciudad="Puebla",
            codigo=None,
        )
        db.add(sede)
        await db.flush()
        await db.commit()
        return sede.id


async def _crear_usuario(email: str, role: str, sede_id: int | None = None) -> str:
    async with async_session_factory() as db:
        db.add(
            User(
                email=email,
                password_hash=get_password_hash("admin123"),
                nombre="Staff",
                apellido_paterno="Prueba",
                role=role,
                es_tutor=False,
                is_active=True,
                sede_id=sede_id,
            )
        )
        await db.commit()
    return email


async def _token(client: AsyncClient, email: str, password: str = "admin123") -> str:
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _telefono(prefijo: str = "222") -> str:
    return f"{prefijo}{uuid.uuid4().int % 10000000:07d}"


def _datos_registro(email: str, telefono: str, sede_id: int) -> dict:
    return {
        "email": email,
        "password": "secreta123",
        "nombre": "Ana",
        "apellido_paterno": "Pérez",
        "apellido_materno": "Gómez",
        "telefono": telefono,
        "sede_id": sede_id,
        "nivel": "PREPA",
    }


@pytest.mark.asyncio
async def test_registro_devuelve_matricula_y_deja_evento():
    sede_id = await _sede_de_pruebas("Q")
    unique = uuid.uuid4().hex[:8]
    email = f"registro-{unique}@example.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(email, _telefono("222"), sede_id),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["matricula"]
        assert body["estatus"] == "registrado"
        assert body["anio"] == 2026
        assert body["qr_token"]
        assert body["pase_url"].startswith("http")

        me = await client.get("/api/v1/inscripciones/me", headers={
            "Authorization": f"Bearer {await _token(client, email, 'secreta123')}"
        })
        assert me.status_code == 200
        assert me.json()["matricula"] == body["matricula"]

    async with async_session_factory() as db:
        student = (await db.execute(select(Student).where(Student.email == email))).scalar_one()
        eventos = (
            await db.execute(
                select(EventoInscripcion).where(EventoInscripcion.student_id == student.id)
            )
        ).scalars().all()
        assert [evento.tipo for evento in eventos] == ["registro"]
        assert eventos[0].detalle["origen"] == "web"


@pytest.mark.asyncio
async def test_registro_rechaza_duplicados():
    sede_id = await _sede_de_pruebas("Q")
    unique = uuid.uuid4().hex[:8]
    email = f"dup-{unique}@example.com"
    telefono = _telefono("222")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        primero = await client.post(
            "/api/v1/auth/register", json=_datos_registro(email, telefono, sede_id)
        )
        assert primero.status_code == 201

        mismo_correo = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(email, _telefono("222"), sede_id),
        )
        assert mismo_correo.status_code == 409
        assert "Email ya registrado" in mismo_correo.json()["detail"]

        mismo_telefono = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"otro-{unique}@example.com", telefono, sede_id),
        )
        assert mismo_telefono.status_code == 409
        assert "Teléfono ya registrado" in mismo_telefono.json()["detail"]


@pytest.mark.asyncio
async def test_registro_cerrado_responde_403():
    sede_id = await _sede_de_pruebas("Q")
    unique = uuid.uuid4().hex[:8]
    admin = await _crear_usuario(f"admin-cierre-{unique}@example.com", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {await _token(client, admin)}"}
        config = await client.put(
            "/api/v1/inscripciones/config", headers=headers, json={"registro_abierto": False}
        )
        assert config.status_code == 200
        assert config.json()["registro_abierto"] is False

        response = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"cerrado-{unique}@example.com", _telefono("222"), sede_id),
        )
        assert response.status_code == 403
        assert "cerrado" in response.json()["detail"].lower()

        await client.put(
            "/api/v1/inscripciones/config", headers=headers, json={"registro_abierto": True}
        )


@pytest.mark.asyncio
async def test_sede_sin_codigo_no_permite_registro():
    sede_id = await _crear_sede(con_codigo=False)
    unique = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"sin-codigo-{unique}@example.com", _telefono("222"), sede_id),
        )
        assert response.status_code == 400
        assert "código de matrícula" in response.json()["detail"]


@pytest.mark.asyncio
async def test_padron_filtra_por_sede_del_rol_inscripcion():
    sede_id = await _sede_de_pruebas("Q")
    otra_sede_id = await _sede_de_pruebas("R")
    unique = uuid.uuid4().hex[:8]
    staff = await _crear_usuario(f"sede-padron-{unique}@example.com", "inscripcion", sede_id)
    admin = await _crear_usuario(f"admin-padron-{unique}@example.com", "admin")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sede_headers = {"Authorization": f"Bearer {await _token(client, staff)}"}
        admin_headers = {"Authorization": f"Bearer {await _token(client, admin)}"}

        await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"padron-{unique}@example.com", _telefono("222"), sede_id),
        )
        await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"padron-otra-{unique}@example.com", _telefono("222"), otra_sede_id),
        )

        padron_sede = await client.get(
            "/api/v1/inscripciones", headers=sede_headers, params={"page_size": 200}
        )
        assert padron_sede.status_code == 200
        assert all(item["sede_id"] == sede_id for item in padron_sede.json()["items"])

        padron_admin = await client.get(
            "/api/v1/inscripciones", headers=admin_headers, params={"page_size": 200}
        )
        sedes = {item["sede_id"] for item in padron_admin.json()["items"]}
        assert sede_id in sedes and otra_sede_id in sedes

        exportado = await client.get(
            "/api/v1/inscripciones/export.csv", headers=sede_headers
        )
        assert exportado.status_code == 403


@pytest.mark.asyncio
async def test_checkin_es_idempotente_y_bloquea_cancelados():
    sede_id = await _sede_de_pruebas("Q")
    unique = uuid.uuid4().hex[:8]
    admin = await _crear_usuario(f"admin-checkin-{unique}@example.com", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {await _token(client, admin)}"}
        registro = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"checkin-{unique}@example.com", _telefono("222"), sede_id),
        )
        matricula = registro.json()["matricula"]
        student_id = registro.json()["student_id"]

        primero = await client.post(
            "/api/v1/inscripciones/checkin", headers=headers, json={"identificador": matricula}
        )
        assert primero.status_code == 200
        assert primero.json()["ya_registrado"] is False

        segundo = await client.post(
            "/api/v1/inscripciones/checkin", headers=headers, json={"identificador": matricula}
        )
        assert segundo.status_code == 200
        assert segundo.json()["ya_registrado"] is True

        await client.patch(
            f"/api/v1/inscripciones/{student_id}/estatus",
            headers=headers,
            json={"estatus": "cancelado"},
        )
        tercero = await client.post(
            "/api/v1/inscripciones/checkin", headers=headers, json={"identificador": matricula}
        )
        assert tercero.status_code == 409

    async with async_session_factory() as db:
        eventos = (
            await db.execute(
                select(EventoInscripcion).where(EventoInscripcion.student_id == student_id)
            )
        ).scalars().all()
        checkins = [evento for evento in eventos if evento.tipo == "checkin"]
        assert len(checkins) == 1


@pytest.mark.asyncio
async def test_cambio_de_estatus_deja_evento():
    sede_id = await _sede_de_pruebas("Q")
    unique = uuid.uuid4().hex[:8]
    admin = await _crear_usuario(f"admin-estatus-{unique}@example.com", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {await _token(client, admin)}"}
        registro = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"estatus-{unique}@example.com", _telefono("222"), sede_id),
        )
        student_id = registro.json()["student_id"]

        response = await client.patch(
            f"/api/v1/inscripciones/{student_id}/estatus",
            headers=headers,
            json={"estatus": "en_inscripcion", "motivo": "se-undio"},
        )
        assert response.status_code == 200
        assert response.json()["estatus"] == "en_inscripcion"

    async with async_session_factory() as db:
        eventos = (
            await db.execute(
                select(EventoInscripcion).where(EventoInscripcion.student_id == student_id)
            )
        ).scalars().all()
        cambios = [evento for evento in eventos if evento.tipo == "cambio_estatus"]
        assert cambios[0].estado_anterior == "registrado"
        assert cambios[0].estado_nuevo == "en_inscripcion"
        assert cambios[0].detalle["motivo"] == "se-undio"


@pytest.mark.asyncio
async def test_simulacro_es_opcional_y_genera_un_solo_cargo():
    sede_id = await _sede_de_pruebas("Q")
    unique = uuid.uuid4().hex[:8]
    admin = await _crear_usuario(f"admin-pagos-{unique}@example.com", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_headers = {"Authorization": f"Bearer {await _token(client, admin)}"}
        await client.put(
            "/api/v1/inscripciones/config",
            headers=admin_headers,
            json={"transferencia_habilitada": True, "simulacro_activo": True},
        )

        registro = await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"pagos-{unique}@example.com", _telefono("222"), sede_id),
        )
        assert registro.status_code == 201
        email = f"pagos-{unique}@example.com"
        alumno_headers = {
            "Authorization": f"Bearer {await _token(client, email, 'secreta123')}"
        }

        me = await client.get("/api/v1/inscripciones/me", headers=alumno_headers)
        assert me.json()["cargos"] == []
        assert me.json()["saldo"] == 0

        opt_in = await client.post("/api/v1/pagos/simulacro", headers=alumno_headers)
        assert opt_in.status_code == 200
        cargo = opt_in.json()["cargo"]
        assert cargo["estado"] == "pendiente"

        repetido = await client.post("/api/v1/pagos/simulacro", headers=alumno_headers)
        assert repetido.json()["creado"] is False
        assert repetido.json()["cargo"]["id"] == cargo["id"]

        efectivo = await client.post(
            "/api/v1/pagos",
            headers=alumno_headers,
            json={"cargo_id": cargo["id"], "monto": cargo["monto"], "metodo": "efectivo"},
        )
        assert efectivo.status_code == 403
        assert "transferencia" in efectivo.json()["detail"].lower()

        transferencia = await client.post(
            "/api/v1/pagos",
            headers=alumno_headers,
            json={
                "cargo_id": cargo["id"],
                "monto": cargo["monto"],
                "metodo": "transferencia",
                "referencia": "TRANSFER-1",
            },
        )
        assert transferencia.status_code == 201
        pago = transferencia.json()
        assert pago["estado"] == "pendiente"

        validado = await client.post(
            f"/api/v1/pagos/{pago['id']}/validar",
            headers=admin_headers,
            json={"aprobado": True},
        )
        assert validado.status_code == 409
        assert "comprobante" in validado.json()["detail"]

        rechazado = await client.post(
            f"/api/v1/pagos/{pago['id']}/validar",
            headers=admin_headers,
            json={"aprobado": False, "motivo": "Comprobante ilegible"},
        )
        assert rechazado.status_code == 200
        assert rechazado.json()["estado"] == "rechazado"

        recibo = await client.get(f"/api/v1/pagos/{pago['id']}/recibo", headers=alumno_headers)
        assert recibo.status_code == 409

        await client.put(
            "/api/v1/inscripciones/config",
            headers=admin_headers,
            json={"transferencia_habilitada": False},
        )


@pytest.mark.asyncio
async def test_subir_comprobante_sin_r2_responde_503():
    sede_id = await _sede_de_pruebas("Q")
    unique = uuid.uuid4().hex[:8]
    admin = await _crear_usuario(f"admin-r2-{unique}@example.com", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_headers = {"Authorization": f"Bearer {await _token(client, admin)}"}
        await client.put(
            "/api/v1/inscripciones/config",
            headers=admin_headers,
            json={"transferencia_habilitada": True, "simulacro_activo": True},
        )
        await client.post(
            "/api/v1/auth/register",
            json=_datos_registro(f"r2-{unique}@example.com", _telefono("222"), sede_id),
        )
        email = f"r2-{unique}@example.com"
        alumno_headers = {
            "Authorization": f"Bearer {await _token(client, email, 'secreta123')}"
        }
        opt_in = await client.post("/api/v1/pagos/simulacro", headers=alumno_headers)
        cargo = opt_in.json()["cargo"]
        pago = await client.post(
            "/api/v1/pagos",
            headers=alumno_headers,
            json={"cargo_id": cargo["id"], "monto": cargo["monto"], "metodo": "transferencia"},
        )
        response = await client.post(
            f"/api/v1/pagos/{pago.json()['id']}/comprobante",
            headers=alumno_headers,
            files={"file": ("comprobante.png", b"falso", "image/png")},
        )
        assert response.status_code == 503
        await client.put(
            "/api/v1/inscripciones/config",
            headers=admin_headers,
            json={"transferencia_habilitada": False},
        )
