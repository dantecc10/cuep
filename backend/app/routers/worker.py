from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.core.database import get_async_db
from app.core.dependencies import verify_worker_key
from app.models.corrida import CorridaHorario

router = APIRouter(prefix="/worker", tags=["worker"])


def _check_key(x_worker_key: str | None):
    if not verify_worker_key(x_worker_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Worker key inválida")


@router.get("/tareas")
async def list_tareas(estado: str = "PENDIENTE", limit: int = 1, x_worker_key: str | None = Header(default=None), db: AsyncSession = Depends(get_async_db)):
    _check_key(x_worker_key)
    stmt = select(CorridaHorario).where(CorridaHorario.estado == estado).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [{"id": c.id, "config_hash": c.config_hash, "parametros_resumen": c.parametros_resumen} for c in items]


@router.post("/tareas/{corrida_id}/iniciar")
async def iniciar(corrida_id: int, x_worker_key: str | None = Header(default=None), db: AsyncSession = Depends(get_async_db)):
    _check_key(x_worker_key)
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    if corrida.estado != "PENDIENTE":
        raise HTTPException(status_code=409, detail="Corrida no disponible")
    corrida.estado = "PROCESANDO"
    corrida.intentos += 1
    await db.flush()
    return {"id": corrida.id, "estado": corrida.estado}


@router.post("/tareas/{corrida_id}/progreso")
async def progreso(corrida_id: int, payload: dict, x_worker_key: str | None = Header(default=None), db: AsyncSession = Depends(get_async_db)):
    _check_key(x_worker_key)
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    corrida.progreso = int(payload.get("progreso", corrida.progreso))
    corrida.etapa = payload.get("etapa", corrida.etapa)
    await db.flush()
    return {"id": corrida.id, "progreso": corrida.progreso, "etapa": corrida.etapa}


@router.post("/tareas/{corrida_id}/resultado")
async def resultado(corrida_id: int, payload: dict, x_worker_key: str | None = Header(default=None), db: AsyncSession = Depends(get_async_db)):
    _check_key(x_worker_key)
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    corrida.estado = payload.get("estado", "COMPLETADO")
    corrida.resultado_json = payload.get("resultado_json")
    corrida.metricas_optimizacion = payload.get("metricas_optimizacion")
    corrida.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"id": corrida.id, "estado": corrida.estado}


@router.post("/tareas/{corrida_id}/error")
async def error(corrida_id: int, payload: dict, x_worker_key: str | None = Header(default=None), db: AsyncSession = Depends(get_async_db)):
    _check_key(x_worker_key)
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    corrida.estado = "ERROR"
    corrida.resultado_json = {"error": payload.get("detalle")}
    await db.flush()
    return {"id": corrida.id, "estado": corrida.estado}
