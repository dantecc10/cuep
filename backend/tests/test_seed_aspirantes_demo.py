from seeds.seed_aspirantes_demo import (
    canonical_area,
    load_source_rows,
    sede_code_for_location,
    select_rows,
)


def test_source_rows_are_parsed_from_real_form():
    rows = load_source_rows()

    assert len(rows) == 99
    assert all(row.nombre and row.apellido_paterno for row in rows)
    assert all(row.email.endswith("@cuep.example.com") for row in rows)
    assert len({row.email for row in rows}) == len(rows)


def test_selection_covers_all_sedes_and_areas():
    rows = load_source_rows()
    selected = select_rows(rows, 50)

    assert len(selected) == 50
    assert len({row.source_index for row in selected}) == 50
    assert {row.sede_code for row in selected} == {"2", "C", "F", "L", "V", "Z"}
    assert {row.area for row in selected} <= {
        "Ciencias Naturales y de la Salud",
        "Ciencias Sociales",
        "Ingeniería y Ciencias Exactas",
    }


def test_location_and_area_normalization():
    assert sede_code_for_location("7 Sede Virtual (completamente en línea)") == "V"
    assert sede_code_for_location("3 Preparatoria 2 de octubre") == "2"
    assert sede_code_for_location("otro lugar") is None
    assert canonical_area("Económico administrativas") == "Ciencias Sociales"
    assert canonical_area("Ciencias Naturales y Salud") == "Ciencias Naturales y de la Salud"


def test_selected_payload_keeps_traceability():
    selected = select_rows(load_source_rows(), 3)
    payload = selected[0].inscripcion(1, solicita_simulacro=True)

    assert payload.email == selected[0].email
    assert payload.sede_id == 1
    assert payload.nivel == "LICENCIATURA"
    assert payload.solicita_simulacro is True
    assert selected[0].source_index > 0
