import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_login_invalid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nope@example.com", "password": "wrong"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body or body.get("requires_2fa") is True


@pytest.mark.asyncio
async def test_register_student():
    email = f"student-{uuid.uuid4().hex[:8]}@example.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sedes = await client.get("/api/v1/sedes")
        assert sedes.status_code == 200
        sede = next(
            item for item in sedes.json() if item.get("activo") and item.get("codigo")
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "stud123",
                "nombre": "Alumno",
                "apellido_paterno": "Demo",
                "sede_id": sede["id"],
                "nivel": "PREPA",
            },
        )
        assert response.status_code == 201

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "stud123"},
        )
        assert login.status_code == 200
