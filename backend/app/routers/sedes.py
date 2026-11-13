from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, select

from app.core.database import get_async_db
from app.core.dependencies import require_role, get_current_user, get_current_user_optional, can_manage_sede
from app.models.sede import Sede, Grupo
from app.models.user import User
from app.models.corrida import CorridaHorario
from app.models.student import Student
from app.schemas.sede import (
    SedeCreate,
    SedeRead,
    GrupoCreate,
    GrupoRead,
)
from app.schemas.enrollment import EnrollmentSettingsUpdate

router = APIRouter(prefix="/sedes", tags=["sedes"])


@router.get("", response_model=list[SedeRead])
async def list_sedes(
    include_deleted: bool = Query(default=False),
    include_inactive: bool = Query(default=False),
    search: str | None = Query(default=None),
    activo: bool | None = Query(default=None),
    sort_by: str = Query(default="nombre"),
    sort_dir: str = Query(default="asc"),
    db: AsyncSession = Depends(get_async_db),
    user: User | None = Depends(get_current_user_optional),
):
    stmt = select(Sede)
    if not include_deleted or (user is None or user.role != "admin"):
        stmt = stmt.where(Sede.deleted_at.is_(None))
    if not include_inactive or (user is None or user.role != "admin"):
        stmt = stmt.where(Sede.activo.isnot(False))
    elif activo is not None:
        stmt = stmt.where(Sede.activo == activo)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Sede.nombre.ilike(term),
                Sede.ciudad.ilike(term),
                Sede.codigo.ilike(term),
            )
        )
    sort_fields = {
        "nombre": Sede.nombre,
        "ciudad": Sede.ciudad,
        "codigo": Sede.codigo,
        "id": Sede.id,
    }
    sort_column = sort_fields.get(sort_by, Sede.nombre)
    stmt = stmt.order_by(sort_column.desc() if sort_dir.lower() == "desc" else sort_column.asc())
    result = await db.execute(stmt)
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
    if sede is None or sede.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    for field in ["nombre", "ciudad", "codigo", "descripcion", "maps_url", "image_url", "activo", "waitlist_enabled", "payment_enabled", "payment_amount", "payment_currency"]:
        if hasattr(payload, field):
            value = getattr(payload, field)
            if value is not None:
                setattr(sede, field, value)
    await db.flush()
    await db.refresh(sede)
    return sede


@router.delete("/{sede_id}", status_code=204)
async def delete_sede(sede_id: int, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    sede = await db.get(Sede, sede_id)
    if sede is None or sede.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    has_deps = False
    for model in (Grupo, CorridaHorario, Student):
        result = await db.execute(select(func.count()).select_from(model).where(model.sede_id == sede_id))
        if int(result.scalar() or 0) > 0:
            has_deps = True
            break
    if has_deps:
        sede.deleted_at = datetime.now(timezone.utc)
        sede.activo = False
        await db.flush()
        return None
    await db.delete(sede)
    await db.flush()
    return None


@router.post("/{sede_id}/restore", response_model=SedeRead)
async def restore_sede(sede_id: int, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    sede = await db.get(Sede, sede_id)
    if sede is None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    sede.deleted_at = None
    sede.activo = True
    await db.flush()
    await db.refresh(sede)
    return sede


@router.get("/{sede_id}/grupos", response_model=list[GrupoRead])
async def list_grupos(sede_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Grupo).where(Grupo.sede_id == sede_id, Grupo.deleted_at.is_(None)))
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


@router.delete("/grupos/{grupo_id}", status_code=204)
async def delete_grupo(grupo_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    grupo = await db.get(Grupo, grupo_id)
    if grupo is None or grupo.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    if not can_manage_sede(user, grupo.sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    grupo.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None


@router.put("/enrollment-settings/{sede_id}")
async def update_enrollment_settings(sede_id: int, payload: EnrollmentSettingsUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if not can_manage_sede(user, sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    sede = await db.get(Sede, sede_id)
    if sede is None or sede.deleted_at is not None:
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
