from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import time
from typing import Sequence

TUTORS_PER_SEDE = 30
EMAIL_DOMAIN = "cuep.example.com"
PASSWORD_ENV = "SEED_TUTOR_PASSWORD"

SEDE_CODES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


@dataclass(frozen=True)
class SedeSpec:
    nombre: str
    codigo: str
    ciudad: str = "Puebla"
    descripcion: str = ""


@dataclass(frozen=True)
class MateriaSpec:
    nombre: str
    nivel: str
    area: str


@dataclass(frozen=True)
class PlanSpec:
    nombre: str
    nivel: str
    area: str
    materias: tuple[str, ...]
    descripcion: str = ""


@dataclass(frozen=True)
class TutorSpec:
    sede_codigo: str
    sede_nombre: str
    index: int
    order: int
    email: str
    nombre: str
    apellido_paterno: str
    apellido_materno: str = "Demo"


SEDES_DEMO: tuple[SedeSpec, ...] = (
    SedeSpec(
        nombre="Preparatoria 2 de Octubre",
        codigo="2",
        descripcion="Sede preparatoria del CUEP.",
    ),
    SedeSpec(
        nombre='Preparatoria "Gral. Lázaro Cárdenas del Río"',
        codigo="L",
        descripcion="Sede preparatoria del CUEP.",
    ),
    SedeSpec(
        nombre='Preparatoria "Alfonso Calderón Moreno"',
        codigo="F",
        descripcion="Sede preparatoria del CUEP.",
    ),
    SedeSpec(
        nombre='Casa de Estudiantes "Emiliano Zapata"',
        codigo="Z",
        descripcion="Casa de estudiantes del CUEP.",
    ),
    SedeSpec(
        nombre="Sede Centro",
        codigo="C",
        descripcion="Sede demo para pruebas del CUEP.",
    ),
    SedeSpec(
        nombre="Sede Virtual",
        codigo="V",
        descripcion="Sede demo para pruebas remotas del CUEP.",
    ),
)


MATERIAS_DEMO: tuple[MateriaSpec, ...] = (
    MateriaSpec("Pensamiento Matemático", "PREPA", "Exactas"),
    MateriaSpec("Matemáticas", "PREPA", "Prepas"),
    MateriaSpec("Lectura y Redacción", "PREPA", "Sociales"),
    MateriaSpec("Español", "PREPA", "Prepas"),
    MateriaSpec("Ciencias Naturales", "PREPA", "Prepas"),
    MateriaSpec("Ciencias Sociales", "PREPA", "Prepas"),
    MateriaSpec("Álgebra", "PREPA", "Prepas"),
    MateriaSpec("Geometría y Trigonometría", "PREPA", "Prepas"),
    MateriaSpec("Física", "PREPA", "Prepas"),
    MateriaSpec("Química", "PREPA", "Prepas"),
    MateriaSpec("Historia de México", "PREPA", "Prepas"),
    MateriaSpec("Inglés", "PREPA", "Prepas"),
    MateriaSpec("Programacion I", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Programacion II", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Ensamblador", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Arquitectura de Computadoras", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Estructuras de Datos", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Cálculo Diferencial", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Cálculo Integral", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Álgebra Lineal", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Ecuaciones Diferenciales", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Probabilidad y Estadística", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Física Mecánica", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Métodos Numéricos", "LICENCIATURA", "Ingenieria y Ciencias Exactas"),
    MateriaSpec("Derecho Romano", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Introduccion al Derecho", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Filosofia del Derecho", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Penal", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Fiscal", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Civil", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Mercantil", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Laboral", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Constitucional", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Administrativo", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Derecho Internacional", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Metodología Jurídica", "LICENCIATURA", "Ciencias Sociales"),
    MateriaSpec("Anatomia", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Biologia", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Analisis Clinico", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Psicologia Clinica", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Fisiología", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Bioquímica", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Microbiología", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Farmacología", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Epidemiología", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Salud Pública", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec("Bioética", "LICENCIATURA", "Ciencias Naturales y de la Salud"),
    MateriaSpec(
        "Metodología de la Investigación en Salud",
        "LICENCIATURA",
        "Ciencias Naturales y de la Salud",
    ),
)


PREPA_MATERIAS = (
    "Pensamiento Matemático",
    "Matemáticas",
    "Lectura y Redacción",
    "Español",
    "Ciencias Naturales",
    "Ciencias Sociales",
    "Álgebra",
    "Geometría y Trigonometría",
    "Física",
    "Química",
    "Historia de México",
    "Inglés",
)

INGENIERIA_MATERIAS = (
    "Programacion I",
    "Programacion II",
    "Ensamblador",
    "Arquitectura de Computadoras",
    "Estructuras de Datos",
    "Cálculo Diferencial",
    "Cálculo Integral",
    "Álgebra Lineal",
    "Ecuaciones Diferenciales",
    "Probabilidad y Estadística",
    "Física Mecánica",
    "Métodos Numéricos",
)

DERECHO_MATERIAS = (
    "Derecho Romano",
    "Introduccion al Derecho",
    "Filosofia del Derecho",
    "Derecho Penal",
    "Derecho Fiscal",
    "Derecho Civil",
    "Derecho Mercantil",
    "Derecho Laboral",
    "Derecho Constitucional",
    "Derecho Administrativo",
    "Derecho Internacional",
    "Metodología Jurídica",
)

MEDICINA_MATERIAS = (
    "Anatomia",
    "Biologia",
    "Analisis Clinico",
    "Psicologia Clinica",
    "Fisiología",
    "Bioquímica",
    "Microbiología",
    "Farmacología",
    "Epidemiología",
    "Salud Pública",
    "Bioética",
    "Metodología de la Investigación en Salud",
)


PLANES_DEMO: tuple[PlanSpec, ...] = (
    PlanSpec(
        nombre="Prepas",
        nivel="PREPA",
        area="Prepas",
        materias=PREPA_MATERIAS,
    ),
    PlanSpec(
        nombre="Nivel Superior",
        nivel="PREPA",
        area="Prepas",
        materias=PREPA_MATERIAS,
    ),
    PlanSpec(
        nombre="Ingenieria en Ciencias de la Computacion",
        nivel="LICENCIATURA",
        area="Ingenieria y Ciencias Exactas",
        materias=INGENIERIA_MATERIAS,
    ),
    PlanSpec(
        nombre="Licenciatura en Derecho",
        nivel="LICENCIATURA",
        area="Ciencias Sociales",
        materias=DERECHO_MATERIAS,
    ),
    PlanSpec(
        nombre="Licenciatura en Medicina",
        nivel="LICENCIATURA",
        area="Ciencias Naturales y de la Salud",
        materias=MEDICINA_MATERIAS,
    ),
)


PLAN_POOLS: tuple[tuple[str, str], ...] = (
    ("Prepas", "Prepas"),
    ("Ingenieria en Ciencias de la Computacion", "Ingenieria y Ciencias Exactas"),
    ("Licenciatura en Derecho", "Ciencias Sociales"),
    ("Licenciatura en Medicina", "Ciencias Naturales y de la Salud"),
)


MATERIA_BY_KEY = {(materia.nombre, materia.nivel): materia for materia in MATERIAS_DEMO}
PLAN_BY_NAME = {plan.nombre: plan for plan in PLANES_DEMO}


def normalize_name(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return " ".join(ascii_value.casefold().split())


def tutor_email(codigo: str, index: int) -> str:
    if not codigo:
        raise ValueError("La sede necesita código para generar emails.")
    if index < 1 or index > TUTORS_PER_SEDE:
        raise ValueError(f"El índice de tutor debe estar entre 1 y {TUTORS_PER_SEDE}.")
    return f"tutor-{codigo.lower()}-{index:02d}@{EMAIL_DOMAIN}"


def build_tutor_specs(sedes: Sequence[tuple[str, str]]) -> list[TutorSpec]:
    codes = [codigo for codigo, _ in sedes]
    if len(codes) != len(set(codes)):
        raise ValueError("Los códigos de sede deben ser únicos.")
    specs: list[TutorSpec] = []
    for sede_index, (codigo, nombre) in enumerate(sedes):
        for index in range(1, TUTORS_PER_SEDE + 1):
            order = sede_index * TUTORS_PER_SEDE + index - 1
            specs.append(
                TutorSpec(
                    sede_codigo=codigo,
                    sede_nombre=nombre,
                    index=index,
                    order=order,
                    email=tutor_email(codigo, index),
                    nombre=f"Tutor {nombre}",
                    apellido_paterno=f"{index:02d}",
                )
            )
    return specs


def availability_block(
    start: time, end: time, tutor_index: int, day_offset: int
) -> tuple[time, time] | None:
    if start.minute or start.second or end.minute or end.second:
        raise ValueError("El horario del CUEP debe estar en horas completas.")
    span = end.hour - start.hour
    if span < 1:
        return None
    block_hours = min(4, span)
    slots = span - block_hours + 1
    offset = (tutor_index * 2 + day_offset) % slots
    begin_hour = start.hour + offset
    return time(begin_hour, 0), time(begin_hour + block_hours, 0)


def validate_catalog() -> None:
    if len(SEDES_DEMO) != 6:
        raise ValueError("El catálogo demo debe tener 6 sedes.")
    if len({sede.codigo for sede in SEDES_DEMO}) != len(SEDES_DEMO):
        raise ValueError("Hay códigos de sede duplicados.")
    if len({normalize_name(sede.nombre) for sede in SEDES_DEMO}) != len(SEDES_DEMO):
        raise ValueError("Hay nombres de sede duplicados.")

    if len(PLANES_DEMO) != 5:
        raise ValueError("El catálogo demo debe tener 5 planes.")
    if len({(plan.nombre, plan.nivel) for plan in PLANES_DEMO}) != len(PLANES_DEMO):
        raise ValueError("Hay planes duplicados.")
    if len({materia.nombre for materia in MATERIAS_DEMO}) != len(MATERIAS_DEMO):
        raise ValueError("Hay materias demo duplicadas.")

    for plan in PLANES_DEMO:
        if len(plan.materias) < 10:
            raise ValueError(f"El plan {plan.nombre} tiene menos de 10 materias.")
        if len(set(plan.materias)) != len(plan.materias):
            raise ValueError(f"El plan {plan.nombre} tiene materias repetidas.")
        for nombre in plan.materias:
            materia = MATERIA_BY_KEY.get((nombre, plan.nivel))
            if materia is None:
                raise ValueError(
                    f"La materia {nombre!r} no existe para el nivel {plan.nivel}."
                )

    specs = build_tutor_specs([(sede.codigo, sede.nombre) for sede in SEDES_DEMO])
    if len(specs) != 180:
        raise ValueError("El catálogo demo debe generar 180 tutores.")
    if len({spec.email for spec in specs}) != len(specs):
        raise ValueError("Hay emails de tutor duplicados.")
    if any(not spec.email.endswith(f"@{EMAIL_DOMAIN}") for spec in specs):
        raise ValueError(f"Todos los emails demo deben usar el dominio {EMAIL_DOMAIN}.")
