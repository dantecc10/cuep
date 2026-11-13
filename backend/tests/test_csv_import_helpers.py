import io

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from app.services.csv_import import (
    _check_lengths,
    _first_available_code,
    _friendly_db_error,
    _normalize_header,
    _parse_bool,
    _read_rows,
    build_template,
)
from app.schemas.imports import ImportReport


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


def test_check_lengths_reports_friendly_row_errors():
    report = ImportReport(entidad="sedes", total=1)
    valid = _check_lengths(
        report,
        2,
        "sedes",
        {"nombre": "x" * 151, "ciudad": "Puebla", "codigo": "A"},
    )
    assert valid is False
    assert report.fallidas == 1
    assert "nombre" in report.errores[0].mensaje
    assert "151" in report.errores[0].mensaje


def test_friendly_db_error_hides_raw_sql():
    truncation = _friendly_db_error(RuntimeError("value too long for type character varying(500)"))
    duplicate = _friendly_db_error(RuntimeError("duplicate key value violates unique constraint"))
    fallback = _friendly_db_error(RuntimeError("boom"))
    assert "demasiado largo" in truncation
    assert "único" in duplicate
    assert "inválido" in fallback
    assert "character varying" not in truncation


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
