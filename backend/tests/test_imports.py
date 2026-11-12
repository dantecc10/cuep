import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE = "http://test"


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url=BASE)


async def _admin_token(client: AsyncClient) -> str:
    try:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"No hay base de datos disponible para las pruebas: {exc}")
    if response.status_code != 200 or "access_token" not in response.json():
        pytest.skip("Se requiere el usuario admin sembrado para probar importaciones.")
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_import_template_requires_auth():
    async with await _client() as client:
        response = await client.get("/api/v1/imports/materias/template")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_import_materias_partial_and_duplicates():
    async with await _client() as client:
        token = await _admin_token(client)
        unique = uuid.uuid4().hex[:8]
        content = (
            "nombre,nivel,area,descripcion\n"
            f"Materia válida {unique},PREPA,Exactas,Descripción\n"
            f"Materia sin área {unique},PREPA,,Falta el área\n"
        )
        files = {"file": ("materias.csv", content, "text/csv")}
        first = await client.post("/api/v1/imports/materias", files=files, headers=_auth(token))
        assert first.status_code == 200, first.text
        report = first.json()
        assert report["creadas"] == 1
        assert report["fallidas"] == 1
        assert report["omitidas"] == 0

        second = await client.post("/api/v1/imports/materias", files=files, headers=_auth(token))
        assert second.status_code == 200, second.text
        report = second.json()
        assert report["creadas"] == 1
        assert report["omitidas"] == 1
        assert report["fallidas"] == 1


@pytest.mark.asyncio
async def test_import_plan_creates_missing_materia():
    async with await _client() as client:
        token = await _admin_token(client)
        unique = uuid.uuid4().hex[:8]
        plan_name = f"Plan {unique}"
        materia_name = f"Materia del plan {unique}"
        content = (
            "nombre,nivel,area,descripcion,materias\n"
            f"{plan_name},PREPA,General,Plan de prueba,{materia_name}\n"
        )
        response = await client.post(
            "/api/v1/imports/planes",
            files={"file": ("planes.csv", content, "text/csv")},
            headers=_auth(token),
        )
        assert response.status_code == 200, response.text
        report = response.json()
        assert report["creadas"] == 1
        assert any(item["tipo"] == "materia" and item["nombre"] == materia_name for item in report["creadas_relacionadas"])

        materias = await client.get("/api/v1/materias", headers=_auth(token))
        names = {item["nombre"] for item in materias.json()}
        assert materia_name in names


@pytest.mark.asyncio
async def test_import_sede_assigns_code_with_warning():
    async with await _client() as client:
        token = await _admin_token(client)
        unique = uuid.uuid4().hex[:8]
        content = f"nombre,ciudad,codigo,descripcion\nSede {unique},Ciudad,,\n"
        response = await client.post(
            "/api/v1/imports/sedes",
            files={"file": ("sedes.csv", content, "text/csv")},
            headers=_auth(token),
        )
        assert response.status_code == 200, response.text
        report = response.json()
        assert report["creadas"] == 1
        assert len(report["advertencias"]) == 1
        assert "Código asignado automáticamente" in report["advertencias"][0]["mensaje"]


@pytest.mark.asyncio
async def test_import_users_generates_temporary_password():
    async with await _client() as client:
        token = await _admin_token(client)
        unique = uuid.uuid4().hex[:8]
        email = f"tutor-{unique}@example.com"
        content = (
            "email,nombre,apellido_paterno,role\n"
            f"{email},Tutor,Prueba,tutor\n"
        )
        response = await client.post(
            "/api/v1/imports/usuarios",
            files={"file": ("usuarios.csv", content, "text/csv")},
            headers=_auth(token),
        )
        assert response.status_code == 200, response.text
        report = response.json()
        assert report["creadas"] == 1
        assert len(report["credenciales"]) == 1
        credential = report["credenciales"][0]
        assert credential["email"] == email
        assert credential["password_temporal"]
        assert credential["email_enviado"] is True

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": credential["password_temporal"]},
        )
        assert login.status_code == 200


@pytest.mark.asyncio
async def test_coordinator_can_only_import_tutors():
    async with await _client() as client:
        admin_token = await _admin_token(client)
        sedes = (await client.get("/api/v1/sedes", headers=_auth(admin_token))).json()
        sede = next((item for item in sedes if item.get("codigo")), None)
        if sede is None:
            pytest.skip("Se requiere una sede con código para probar al coordinador.")

        unique = uuid.uuid4().hex[:8]
        coordinator_email = f"coord-{unique}@example.com"
        created = await client.post(
            "/api/v1/usuarios",
            json={
                "email": coordinator_email,
                "password": "coord123",
                "nombre": "Coord",
                "apellido_paterno": "Prueba",
                "role": "coordinador",
                "sede_id": sede["id"],
            },
            headers=_auth(admin_token),
        )
        assert created.status_code == 201, created.text

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": coordinator_email, "password": "coord123"},
        )
        assert login.status_code == 200
        coordinator_token = login.json()["access_token"]

        denied_content = (
            "email,nombre,apellido_paterno,role\n"
            f"admin-{unique}@example.com,Admin,Prueba,admin\n"
        )
        denied = await client.post(
            "/api/v1/imports/usuarios",
            files={"file": ("usuarios.csv", denied_content, "text/csv")},
            headers=_auth(coordinator_token),
        )
        assert denied.status_code == 200, denied.text
        assert denied.json()["fallidas"] == 1

        allowed_content = (
            "email,nombre,apellido_paterno,role\n"
            f"tutor-coord-{unique}@example.com,Tutor,Prueba,tutor\n"
        )
        allowed = await client.post(
            "/api/v1/imports/usuarios",
            files={"file": ("usuarios.csv", allowed_content, "text/csv")},
            headers=_auth(coordinator_token),
        )
        assert allowed.status_code == 200, allowed.text
        assert allowed.json()["creadas"] == 1
