from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
from app.core.dependencies import require_role, get_current_user, can_manage_sede
from app.models.sede import Sede, Grupo
from app.models.user import User
from app.schemas.sede import (
    SedeCreate,
    SedeRead,
    GrupoCreate,
    GrupoRead,
)
from app.schemas.enrollment import EnrollmentSettingsUpdate

router = APIRouter(prefix="/sedes", tags=["sedes"])


@router.get("", response_model=list[SedeRead])
async def list_sedes(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Sede))
    return result.scalars().all()


@router.post("", response_model=SedeRead, status_code=201)
async def create_sede(payload: SedeCreate, db: AsyncSession = Depends(get_async_db), user: User = Depends(require_role("admin"))):
    sede = Sede(**payload.model_dump())
    db.add(sede)
    await db.flush()
    await db.refresh(sede)
    return sede


@router.put("/{sede_id}", response_model=SedeRead)
async def update_sede(sede_id: int, payload: SedeCreate, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    sede = await db.get(Sede, sede_id)
    if sede is None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    sede.nombre = payload.nombre
    if payload.ciudad is not None:
        sede.ciudad = payload.ciudad
    await db.flush()
    await db.refresh(sede)
    return sede


@router.delete("/{sede_id}", status_code=204)
async def delete_sede(sede_id: int, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    sede = await db.get(Sede, sede_id)
    if sede is None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    await db.delete(sede)
    await db.flush()
    return None


@router.get("/{sede_id}/grupos", response_model=list[GrupoRead])
async def list_grupos(sede_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Grupo).where(Grupo.sede_id == sede_id))
    return result.scalars().all()


@router.post("/{sede_id}/grupos", response_model=GrupoRead, status_code=201)
async def create_grupo(sede_id: int, payload: GrupoCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if not can_manage_sede(user, sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    grupo = Grupo(sede_id=sede_id, **payload.model_dump())
    db.add(grupo)
    await db.flush()
    await db.refresh(grupo)
    return grupo


@router.put("/enrollment-settings/{sede_id}")
async def update_enrollment_settings(sede_id: int, payload: EnrollmentSettingsUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if not can_manage_sede(user, sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    sede = await db.get(Sede, sede_id)
    if sede is None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    if payload.waitlist_enabled is not None:
        sede.waitlist_enabled = payload.waitlist_enabled
    if payload.payment_enabled is not None:
        sede.payment_enabled = payload.payment_enabled
    if payload.payment_amount is not None:
        sede.payment_amount = payload.payment_amount
    if payload.payment_currency is not None:
        sede.payment_currency = payload.payment_currency
    await db.flush()
    return {"sede_id": sede.id, "waitlist_enabled": sede.waitlist_enabled, "payment_enabled": sede.payment_enabled, "payment_amount": sede.payment_amount, "payment_currency": sede.payment_currency}
