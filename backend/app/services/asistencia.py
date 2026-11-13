from datetime import date, datetime, time, timedelta

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asistencia import SesionClase
from app.models.corrida import CorridaHorario


def parse_time(value: str) -> time:
    value = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Hora inválida: {value}")


def periodos_validos(start: date | None, end: date | None) -> bool:
    return bool(start and end and start <= end)


async def generar_sesiones(
    db: AsyncSession,
    corrida: CorridaHorario,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
) -> int:
    start = fecha_inicio or corrida.fecha_inicio
    end = fecha_fin or corrida.fecha_fin
    if not periodos_validos(start, end) or corrida.sede_id is None:
        return 0

    asignaciones = (corrida.resultado_json or {}).get("asignaciones", [])
    values = []
    current = start
    while current <= end:
        weekday = current.isoweekday()
        for assignment in asignaciones:
            if int(assignment.get("dia", 0)) != weekday:
                continue
            values.append(
                {
                    "corrida_id": corrida.id,
                    "sede_id": corrida.sede_id,
                    "grupo_id": assignment["grupo_id"],
                    "tutor_id": assignment["tutor_id"],
                    "fecha": current,
                    "dia_semana": weekday,
                    "hora_inicio": parse_time(assignment["hora_inicio"]),
                    "hora_fin": parse_time(assignment["hora_fin"]),
                    "estado": "pendiente",
                    "origen": "automatica",
                }
            )
        current += timedelta(days=1)

    if not values:
        return 0

    statement = (
        pg_insert(SesionClase)
        .values(values)
        .on_conflict_do_nothing(index_elements=["grupo_id", "tutor_id", "fecha", "hora_inicio"])
        .returning(SesionClase.id)
    )
    result = await db.execute(statement)
    return len(result.scalars().all())
