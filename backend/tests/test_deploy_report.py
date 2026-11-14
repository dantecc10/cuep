import importlib.util
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parents[2] / "scripts" / "deploy_report.py"


@pytest.fixture(scope="module")
def reporte():
    spec = importlib.util.spec_from_file_location("deploy_report", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_detecta_la_revision_mas_reciente(reporte):
    revision = reporte.revision_actual()
    assert revision
    assert revision[0].isalnum()


def test_el_reporte_expone_las_variables_esperadas(reporte):
    nombres = {nombre for nombre, _modulo, _criticidad, _ejemplos in reporte.VARIABLES}
    for esperada in (
        "DATABASE_URL",
        "PUBLIC_APP_URL",
        "R2_PRIVATE_BUCKET",
        "SMTP_HOST",
        "EMAIL_DEV_MODE",
        "JWT_SECRET",
        "WORKER_API_KEY",
    ):
        assert esperada in nombres


def test_lee_el_archivo_de_entorno(reporte):
    env = reporte.leer_env()
    assert isinstance(env, dict)
    assert "DATABASE_URL" in env


def test_clasifica_el_estado_de_las_variables(reporte):
    assert reporte.OK == 0
    assert reporte.AVISO == 1
    assert reporte.FALLA == 2
