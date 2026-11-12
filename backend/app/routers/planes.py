from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
from app.core.dependencies import require_role
from app.models.plan import PlanEstudio, plan_materias
from app.models.materia import Materia
from app.models.user import User
from app.schemas.plan import PlanEstudioCreate, PlanEstudioRead, PlanEstudioUpdate, PlanMateriaUpdate
from app.schemas.materia import MateriaRead

router = APIRouter(prefix="/planes", tags=["planes"])


@router.get("", response_model=list[PlanEstudioRead])
async def list_planes(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(PlanEstudio).where(PlanEstudio.deleted_at.is_(None)))
    return result.scalars().all()


@router.post("", response_model=PlanEstudioRead, status_code=201)
async def create_plan(payload: PlanEstudioCreate, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    plan = PlanEstudio(**payload.model_dump(), created_by=user.id)
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanEstudioRead)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_async_db)):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


@router.put("/{plan_id}", response_model=PlanEstudioRead)
async def update_plan(plan_id: int, payload: PlanEstudioUpdate, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None or plan.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    changes = payload.model_dump(exclude_unset=True)
    if "nivel" in changes and changes["nivel"] not in ("PREPA", "LICENCIATURA"):
        raise HTTPException(status_code=422, detail="El nivel debe ser PREPA o LICENCIATURA.")
    for field, value in changes.items():
        setattr(plan, field, value)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}/materias", response_model=list[MateriaRead])
async def list_plan_materias(plan_id: int, db: AsyncSession = Depends(get_async_db)):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    result = await db.execute(select(Materia).join(plan_materias).where(plan_materias.c.plan_id == plan_id))
    return result.scalars().all()


@router.put("/{plan_id}/materias")
async def set_plan_materias(plan_id: int, payload: PlanMateriaUpdate, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    await db.execute(plan_materias.delete().where(plan_materias.c.plan_id == plan_id))
    for mid in payload.materia_ids:
        await db.execute(plan_materias.insert().values(plan_id=plan_id, materia_id=mid))
    await db.flush()
    return {"plan_id": plan_id, "materia_ids": payload.materia_ids}


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(plan_id: int, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    plan.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None
