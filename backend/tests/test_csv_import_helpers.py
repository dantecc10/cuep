import io

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.services.csv_import import (
    _first_available_code,
    _normalize_header,
    _parse_bool,
    _read_rows,
    build_template,
)


def test_templates_have_headers_and_bom():
    expected = {
        "sedes": "nombre,ciudad,codigo",
        "materias": "nombre,nivel,area",
        "planes": "nombre,nivel,area",
        "usuarios": "email,nombre,apellido_paterno",
    }
    for entity, header in expected.items():
        template = build_template(entity)
        assert template.startswith("\ufeff")
        assert header in template


def test_header_normalization_handles_accents_and_aliases():
    assert _normalize_header("Código") == "codigo"
    assert _normalize_header("Correo") == "email"
    assert _normalize_header("Sede") == "sede_codigo"
    assert _normalize_header("Apellido Paterno") == "apellido_paterno"


def test_first_available_code():
    assert _first_available_code(set()) == "A"
    assert _first_available_code({"A", "B"}) == "C"


def test_parse_bool():
    assert _parse_bool("sí") is True
    assert _parse_bool("no") is False
    assert _parse_bool(None, default=True) is True
    with pytest.raises(ValueError):
        _parse_bool("quizá")


@pytest.mark.asyncio
async def test_read_rows_detects_semicolon_delimiter():
    data = "nombre;nivel;area\nÁlgebra;PREPA;Exactas\n".encode()
    file = UploadFile(filename="materias.csv", file=io.BytesIO(data))
    rows = await _read_rows(file, {"nombre", "nivel", "area"})
    assert rows == [{"nombre": "Álgebra", "nivel": "PREPA", "area": "Exactas"}]


@pytest.mark.asyncio
async def test_read_rows_reports_missing_columns():
    file = UploadFile(filename="materias.csv", file=io.BytesIO(b"nombre,nivel\nAlgebra,PREPA\n"))
    with pytest.raises(HTTPException) as exc:
        await _read_rows(file, {"nombre", "nivel", "area"})
    assert exc.value.status_code == 422
    assert "area" in str(exc.value.detail)
