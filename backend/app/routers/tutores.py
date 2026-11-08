from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_async_db
from app.core.dependencies import require_role, get_current_user
from app.models.user import User
from app.models.disponibilidad import DisponibilidadTutor, TutorMateria
from app.schemas.tutor import TutorUpdate
from app.schemas.user import UserRead

router = APIRouter(prefix="/tutores", tags=["tutores"])


@router.get("", response_model=list[UserRead])
async def list_tutores(db: AsyncSession = Depends(get_async_db), user=Depends(require_role("admin", "coordinador"))):
    result = await db.execute(select(User).where(User.es_tutor.is_(True)))
    return result.scalars().all()


@router.get("/{tutor_id}", response_model=UserRead)
async def get_tutor(tutor_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.id == tutor_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Tutor no encontrado")
    return user


@router.put("/{tutor_id}/disponibilidad", status_code=204)
async def update_disponibilidad(tutor_id: int, payload: TutorUpdate, db: AsyncSession = Depends(get_async_db), user=Depends(get_current_user)):
    if user.id != tutor_id and user.role not in ("admin", "coordinador"):
        raise HTTPException(status_code=403, detail="No autorizado")
    if payload.disponibilidad is not None:
        await db.execute(delete(DisponibilidadTutor).where(DisponibilidadTutor.tutor_id == tutor_id))
        for d in payload.disponibilidad:
            db.add(DisponibilidadTutor(tutor_id=tutor_id, dia_semana=d.dia_semana, hora_inicio=d.hora_inicio, hora_fin=d.hora_fin))
    if payload.materias is not None:
        await db.execute(delete(TutorMateria).where(TutorMateria.tutor_id == tutor_id))
        for m in payload.materias:
            db.add(TutorMateria(tutor_id=tutor_id, materia_id=m.materia_id, nivel_preferencia=m.nivel_preferencia))
    if payload.carga_max_horas is not None:
        target = await db.get(User, tutor_id)
        if target:
            target.carga_max_horas = payload.carga_max_horas
    if payload.area_principal is not None:
        target = await db.get(User, tutor_id)
        if target:
            target.area_principal = payload.area_principal
    await db.flush()
    return None
