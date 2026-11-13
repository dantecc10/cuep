import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, can_manage_sede
from app.models.corrida import CorridaHorario
from app.models.sede import Grupo
from app.models.user import User
from app.models.disponibilidad import DisponibilidadTutor, TutorMateria
from app.services.horario import cargar_horario, serializar_horario
from app.services.asistencia import generar_sesiones, periodos_validos
from app.schemas.corrida import CorridaCreate, CorridaRead, PublicarCorridaRequest

router = APIRouter(prefix="/corridas", tags=["corridas"])


async def _build_canonical(db: AsyncSession, sede_id: int, grupo_ids: list[int], parametros: dict | None):
    grupos_result = await db.execute(select(Grupo).where(Grupo.sede_id == sede_id, Grupo.id.in_(grupo_ids)))
    grupos = grupos_result.scalars().all()

    tutores_result = await db.execute(select(User).where(User.es_tutor == True))  # noqa: E712
    tutores = tutores_result.scalars().all()

    tutor_list = []
    for t in tutores:
        disp_result = await db.execute(select(DisponibilidadTutor).where(DisponibilidadTutor.tutor_id == t.id))
        tm_result = await db.execute(select(TutorMateria).where(TutorMateria.tutor_id == t.id))
        tutor_list.append({
            "id": t.id,
            "role": t.role,
            "carga_max": t.carga_max_horas,
            "area": t.area_principal,
            "disponibilidad": [{"dia": d.dia_semana, "inicio": d.hora_inicio.strftime("%H:%M"), "fin": d.hora_fin.strftime("%H:%M")} for d in disp_result.scalars().all()],
            "materias": [{"materia_id": m.materia_id, "pref": m.nivel_preferencia, "vetada": m.vetada} for m in tm_result.scalars().all()],
        })

    grupos_list = [{"id": g.id, "materia_id": g.materia_id, "horas_totales": g.horas_totales, "bloque": g.bloque_horas, "capacidad": g.capacidad} for g in grupos]

    horario = serializar_horario(await cargar_horario(db))
    canonical = {
        "sede_id": sede_id,
        "grupos": sorted(grupos_list, key=lambda x: x["id"]),
        "tutores": sorted(tutor_list, key=lambda x: x["id"]),
        "parametros": parametros or {},
        "horario_cuep": horario,
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest(), canonical


@router.post("", response_model=CorridaRead)
async def create_corrida(payload: CorridaCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if not can_manage_sede(user, payload.sede_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")

    config_hash, canonical = await _build_canonical(db, payload.sede_id, payload.grupo_ids, payload.parametros)

    result = await db.execute(select(CorridaHorario).where(CorridaHorario.config_hash == config_hash, CorridaHorario.estado == "COMPLETADO"))
    existing = result.scalar_one_or_none()
    if existing:
        if payload.fecha_inicio or payload.fecha_fin:
            if not periodos_validos(payload.fecha_inicio, payload.fecha_fin):
                raise HTTPException(status_code=400, detail="El periodo debe tener fecha de inicio y fin, con inicio menor o igual al fin")
            existing.fecha_inicio = payload.fecha_inicio
            existing.fecha_fin = payload.fecha_fin
            await db.flush()
        return existing

    result = await db.execute(select(CorridaHorario).where(CorridaHorario.config_hash == config_hash, CorridaHorario.estado.in_(["PENDIENTE", "PROCESANDO"])))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    if (payload.fecha_inicio is None) != (payload.fecha_fin is None):
        raise HTTPException(status_code=400, detail="El periodo debe incluir fecha de inicio y fin")
    if payload.fecha_inicio and not periodos_validos(payload.fecha_inicio, payload.fecha_fin):
        raise HTTPException(status_code=400, detail="La fecha de inicio debe ser menor o igual a la fecha de fin")

    corrida = CorridaHorario(
        sede_id=payload.sede_id,
        config_hash=config_hash,
        estado="PENDIENTE",
        solicitado_por=user.email,
        parametros_resumen=canonical,
        fecha_inicio=payload.fecha_inicio,
        fecha_fin=payload.fecha_fin,
    )
    db.add(corrida)
    await db.flush()
    await db.refresh(corrida)
    return corrida


@router.get("", response_model=list[CorridaRead])
async def list_corridas(sede_id: int | None = None, estado: str | None = None, publicada: bool | None = None, db: AsyncSession = Depends(get_async_db)):
    stmt = select(CorridaHorario).where(CorridaHorario.deleted_at.is_(None))
    if sede_id is not None:
        stmt = stmt.where(CorridaHorario.sede_id == sede_id)
    if estado is not None:
        stmt = stmt.where(CorridaHorario.estado == estado)
    if publicada is not None:
        stmt = stmt.where(CorridaHorario.publicada == publicada)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{corrida_id}", response_model=CorridaRead)
async def get_corrida(corrida_id: int, db: AsyncSession = Depends(get_async_db)):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    return corrida


@router.post("/{corrida_id}/aprobar", response_model=CorridaRead)
async def aprobar_corrida(corrida_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    if not can_manage_sede(user, corrida.sede_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    if corrida.estado != "COMPLETADO":
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar corridas completadas")
    corrida.aprobada = True
    corrida.aprobada_por = user.id
    corrida.aprobada_en = datetime.now(timezone.utc)
    await db.flush()
    return corrida


@router.post("/{corrida_id}/publicar", response_model=CorridaRead)
async def publicar_corrida(corrida_id: int, payload: PublicarCorridaRequest | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    if not can_manage_sede(user, corrida.sede_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    if not corrida.aprobada:
        raise HTTPException(status_code=400, detail="La corrida debe estar aprobada antes de publicarse")
    if payload is not None and (payload.fecha_inicio is not None or payload.fecha_fin is not None):
        if not periodos_validos(payload.fecha_inicio, payload.fecha_fin):
            raise HTTPException(status_code=400, detail="El periodo debe tener fecha de inicio y fin, con inicio menor o igual al fin")
        corrida.fecha_inicio = payload.fecha_inicio
        corrida.fecha_fin = payload.fecha_fin
    # unpublish previous
    result = await db.execute(select(CorridaHorario).where(CorridaHorario.sede_id == corrida.sede_id, CorridaHorario.publicada == True))  # noqa: E712
    for c in result.scalars().all():
        c.publicada = False
    corrida.publicada = True
    corrida.publicada_por = user.id
    corrida.publicada_en = datetime.now(timezone.utc)
    await db.flush()
    await generar_sesiones(db, corrida)
    await db.flush()
    return corrida


@router.post("/{corrida_id}/generar-sesiones")
async def generar_sesiones_corrida(
    corrida_id: int,
    payload: PublicarCorridaRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    if not can_manage_sede(user, corrida.sede_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    if not corrida.publicada:
        raise HTTPException(status_code=400, detail="La corrida debe estar publicada")
    if payload is not None and (payload.fecha_inicio is not None or payload.fecha_fin is not None):
        if not periodos_validos(payload.fecha_inicio, payload.fecha_fin):
            raise HTTPException(status_code=400, detail="El periodo debe tener fecha de inicio y fin, con inicio menor o igual al fin")
        corrida.fecha_inicio = payload.fecha_inicio
        corrida.fecha_fin = payload.fecha_fin
    if not periodos_validos(corrida.fecha_inicio, corrida.fecha_fin):
        raise HTTPException(status_code=400, detail="Define el periodo de la corrida antes de generar sesiones")
    count = await generar_sesiones(db, corrida)
    await db.flush()
    return {"sesiones_generadas": count, "fecha_inicio": corrida.fecha_inicio, "fecha_fin": corrida.fecha_fin}


@router.post("/{corrida_id}/reintentar", response_model=CorridaRead)
async def reintentar(corrida_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    if not can_manage_sede(user, corrida.sede_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    corrida.estado = "PENDIENTE"
    corrida.intentos = 0
    await db.flush()
    return corrida


@router.delete("/{corrida_id}", status_code=204)
async def delete_corrida(corrida_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    corrida = await db.get(CorridaHorario, corrida_id)
    if corrida is None or corrida.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Corrida no encontrada")
    if not can_manage_sede(user, corrida.sede_id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    corrida.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None
