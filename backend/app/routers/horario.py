from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, require_role
from app.models.horario import ConfiguracionHorarioDia
from app.models.user import User
from app.schemas.horario import HorarioConfigUpdate
from app.services.horario import cargar_horario, serializar_horario

router = APIRouter(prefix="/configuracion-horario", tags=["horario"])


@router.get("")
async def get_configuracion(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    return serializar_horario(await cargar_horario(db))


@router.put("")
async def update_configuracion(
    payload: HorarioConfigUpdate,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
    if len(payload.dias) != 7:
        raise HTTPException(status_code=422, detail="Debes enviar los 7 días de la semana")
    days = {item.dia: item for item in payload.dias}
    if len(days) != 7:
        raise HTTPException(status_code=422, detail="Los días no pueden repetirse")
    if not any(item.activo for item in payload.dias):
        raise HTTPException(status_code=422, detail="Debe haber al menos un día activo")
    for item in payload.dias:
        if item.inicio >= item.fin:
            raise HTTPException(status_code=422, detail=f"El rango del día {item.dia} no es válido")
        if item.inicio.minute or item.inicio.second or item.fin.minute or item.fin.second:
            raise HTTPException(status_code=422, detail="Los horarios deben ser en horas completas")
        if item.fin.hour >= 24:
            raise HTTPException(status_code=422, detail="La hora de fin debe ser anterior a medianoche")

    rows_result = await db.execute(select(ConfiguracionHorarioDia))
    existing = {row.dia_semana: row for row in rows_result.scalars().all()}
    result = []
    for day, item in sorted(days.items()):
        row = existing.get(day)
        if row is None:
            row = ConfiguracionHorarioDia(dia_semana=day)
            db.add(row)
        row.activo = item.activo
        row.hora_inicio = item.inicio
        row.hora_fin = item.fin
        row.updated_by = admin.id
        result.append(row)
    await db.flush()
    return serializar_horario(result)
