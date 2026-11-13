from datetime import time

from seeds.demo_catalog import (
    EMAIL_DOMAIN,
    MATERIAS_DEMO,
    PLANES_DEMO,
    SEDES_DEMO,
    TUTORS_PER_SEDE,
    availability_block,
    build_tutor_specs,
    normalize_name,
    validate_catalog,
)


def test_demo_catalog_is_consistent():
    validate_catalog()

    assert len(SEDES_DEMO) == 6
    assert len(PLANES_DEMO) == 5
    assert len(MATERIAS_DEMO) == 48
    assert len({sede.codigo for sede in SEDES_DEMO}) == 6
    assert len({normalize_name(sede.nombre) for sede in SEDES_DEMO}) == 6


def test_every_plan_has_at_least_ten_unique_materias():
    for plan in PLANES_DEMO:
        assert len(plan.materias) == 12
        assert len(set(plan.materias)) == 12


def test_tutor_specs_are_unique_and_use_demo_domain():
    specs = build_tutor_specs([(sede.codigo, sede.nombre) for sede in SEDES_DEMO])

    assert len(specs) == len(SEDES_DEMO) * TUTORS_PER_SEDE == 180
    assert len({spec.email for spec in specs}) == 180
    assert all(spec.email.endswith(f"@{EMAIL_DOMAIN}") for spec in specs)
    assert all(spec.apellido_paterno.isdigit() for spec in specs)


def test_tutor_emails_follow_sede_code_pattern():
    specs = build_tutor_specs([("C", "Sede Centro")])

    assert specs[0].email == "tutor-c-01@cuep.example.com"
    assert specs[-1].email == "tutor-c-30@cuep.example.com"


def test_availability_blocks_stay_inside_cuep_hours():
    start = time(8, 0)
    end = time(20, 0)

    for tutor_index in range(180):
        for day_offset in range(2):
            block = availability_block(start, end, tutor_index, day_offset)
            assert block is not None
            block_start, block_end = block
            assert start <= block_start < block_end <= end
            assert block_end.hour - block_start.hour == 4
