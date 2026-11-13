from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horario import ConfiguracionHorarioDia

DEFAULT_HORARIO = [
    {"dia_semana": 1, "activo": False, "hora_inicio": time(8, 0), "hora_fin": time(20, 0)},
    {"dia_semana": 2, "activo": False, "hora_inicio": time(8, 0), "hora_fin": time(20, 0)},
    {"dia_semana": 3, "activo": False, "hora_inicio": time(8, 0), "hora_fin": time(20, 0)},
    {"dia_semana": 4, "activo": False, "hora_inicio": time(8, 0), "hora_fin": time(20, 0)},
    {"dia_semana": 5, "activo": False, "hora_inicio": time(8, 0), "hora_fin": time(20, 0)},
    {"dia_semana": 6, "activo": True, "hora_inicio": time(8, 0), "hora_fin": time(20, 0)},
    {"dia_semana": 7, "activo": True, "hora_inicio": time(8, 0), "hora_fin": time(20, 0)},
]


async def cargar_horario(db: AsyncSession) -> list[ConfiguracionHorarioDia]:
    result = await db.execute(select(ConfiguracionHorarioDia).order_by(ConfiguracionHorarioDia.dia_semana))
    rows = list(result.scalars().all())
    if rows:
        return rows
    return [
        ConfiguracionHorarioDia(
            dia_semana=item["dia_semana"],
            activo=item["activo"],
            hora_inicio=item["hora_inicio"],
            hora_fin=item["hora_fin"],
        )
        for item in DEFAULT_HORARIO
    ]


def serializar_horario(rows: list[ConfiguracionHorarioDia]) -> list[dict]:
    return [
        {
            "dia": row.dia_semana,
            "activo": row.activo,
            "inicio": row.hora_inicio.strftime("%H:%M"),
            "fin": row.hora_fin.strftime("%H:%M"),
        }
        for row in rows
    ]
