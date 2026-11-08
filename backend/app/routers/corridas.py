import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
from app.core.dependencies import require_role, get_current_user
from app.models.corrida import CorridaHorario
from app.models.sede import Grupo
from app.models.user import User
from app.models.disponibilidad import DisponibilidadTutor, TutorMateria
from app.schemas.corrida import CorridaCreate, CorridaRead

router = APIRouter(prefix="/corridas", tags=["corridas"])


async def _build_canonical(db: AsyncSession, sede_id: int, grupo_ids: list[int], parametros: dict | None):
    grupos_result = await db.execute(select(Grupo).where(Grupo.sede_id == sede_id, Grupo.id.in_(grupo_ids)))
    grupos = grupos_result.scalars().all()

    tutores_result = await db.execute(select(User).where(User.es_tutor.is_(True)))
    tutores = tutores_result.scalars().all()

    tutor_list = []
    for t in tutores:
        disp_result = await db.execute(select(DisponibilidadTutor).where(DisponibilidadTutor.tutor_id == t.id))
        tm_result = await db.execute(select(TutorMateria).where(TutorMateria.tutor_id == t.id))
        tutor_list.append({
            "id": t.id,
            "carga_max": t.carga_max_horas,
            "area": t.area_principal,
            "disponibilidad": [{"dia": d.dia_semana, "inicio": d.hora_inicio.strftime("%H:%M"), "fin": d.hora_fin.strftime("%H:%M")} for d in disp_result.scalars().all()],
            "materias": [{"materia_id": m.materia_id, "pref": m.nivel_preferencia} for m in tm_result.scalars().all()],
        })

    grupos_list = [{"id": g.id, "materia_id": g.materia_id, "horas_totales": g.horas_totales, "bloque": g.bloque_horas, "capacidad": g.capacidad} for g in grupos]

    canonical = {
        "sede_id": sede_id,
        "grupos": sorted(grupos_list, key=lambda x: x["id"]),
        "tutores": sorted(tutor_list, key=lambda x: x["id"]),
        "parametros": parametros or {},
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest(), canonical


@router.post("", response_model=CorridaRead)
async def create_corrida(payload: CorridaCreate, db: AsyncSession = Depends(get_async_db), user=Depends(get_current_user)):
    config_hash, canonical = await _build_canonical(db, payload.sede_id, payload.grupo_ids, payload.parametros)

    # cache hit completed
    result = await db.execute(select(CorridaHorario).where(CorridaHorario.config_hash == config_hash, CorridaHorario.estado == "COMPLETADO"))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # dedup pending/processing
    result = await db.execute(select(CorridaHorario).where(CorridaHorario.config_hash == config_hash, CorridaHorario.estado.in_(["PENDIENTE", "PROCESANDO"])))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    corrida = CorridaHorario(
        config_hash=config_hash,
        estado="PENDIENTE",
        solicitado_por=user.email,
        parametros_resumen=canonical,
    )
    db.add(corrida)
    await db.flush()
    await db.refresh(corrida)
    return corrida


@router.get("", response_model=list[CorridaRead])
async def list_corridas(sede_id: int | None = None, estado: str | None = None, db: AsyncSession = Depends(get_async_db)):
    stmt = select(CorridaHorario)
    if estado:
        stmt = stmt.where(CorridaHorario.estado == estado)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{corrida_id}", response_model=CorridaRead)
async def get_corrida(corrida_id: int, db: AsyncSession = Depends(get_async_db)):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    return corrida


@router.post("/{corrida_id}/reintentar", response_model=CorridaRead)
async def reintentar(corrida_id: int, db: AsyncSession = Depends(get_async_db), user=Depends(require_role("admin", "coordinador"))):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    corrida.estado = "PENDIENTE"
    corrida.intentos = 0
    await db.flush()
    return corrida
