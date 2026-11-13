from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import require_role
from app.models.materia import Materia
from app.models.plan import PlanEstudio, plan_materias
from app.models.user import User
from app.schemas.materia import MateriaRead
from app.schemas.plan import PlanEstudioCreate, PlanEstudioRead, PlanEstudioUpdate, PlanMateriaUpdate

router = APIRouter(prefix="/planes", tags=["planes"])


SORT_FIELDS = {
    "nombre": PlanEstudio.nombre,
    "nivel": PlanEstudio.nivel,
    "area": PlanEstudio.area,
    "id": PlanEstudio.id,
}


@router.get("", response_model=list[PlanEstudioRead])
async def list_planes(
    nivel: str | None = None,
    area: str | None = None,
    search: str | None = Query(default=None),
    activo: bool | None = None,
    sort_by: str = Query(default="nombre"),
    sort_dir: str = Query(default="asc"),
    db: AsyncSession = Depends(get_async_db),
):
    stmt = select(PlanEstudio).where(PlanEstudio.deleted_at.is_(None))
    if nivel:
        stmt = stmt.where(PlanEstudio.nivel == nivel)
    if area:
        stmt = stmt.where(PlanEstudio.area == area)
    if activo is not None:
        stmt = stmt.where(PlanEstudio.activo == activo)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                PlanEstudio.nombre.ilike(term),
                PlanEstudio.area.ilike(term),
                PlanEstudio.descripcion.ilike(term),
            )
        )
    sort_column = SORT_FIELDS.get(sort_by, PlanEstudio.nombre)
    stmt = stmt.order_by(sort_column.desc() if sort_dir.lower() == "desc" else sort_column.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=PlanEstudioRead, status_code=201)
async def create_plan(
    payload: PlanEstudioCreate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
    plan = PlanEstudio(**payload.model_dump(), created_by=user.id)
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanEstudioRead)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_async_db)):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None or plan.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


@router.put("/{plan_id}", response_model=PlanEstudioRead)
async def update_plan(
    plan_id: int,
    payload: PlanEstudioUpdate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
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
    if plan is None or plan.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    result = await db.execute(
        select(Materia)
        .join(plan_materias)
        .where(
            plan_materias.c.plan_id == plan_id,
            Materia.deleted_at.is_(None),
        )
        .order_by(Materia.nombre.asc())
    )
    return result.scalars().all()


@router.put("/{plan_id}/materias")
async def set_plan_materias(
    plan_id: int,
    payload: PlanMateriaUpdate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None or plan.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    unique_ids = list(dict.fromkeys(payload.materia_ids))
    if unique_ids:
        result = await db.execute(
            select(Materia.id).where(Materia.id.in_(unique_ids), Materia.deleted_at.is_(None))
        )
        found = set(result.scalars().all())
        missing = [mid for mid in unique_ids if mid not in found]
        if missing:
            raise HTTPException(status_code=422, detail=f"Materias no válidas: {', '.join(map(str, missing))}")
    await db.execute(delete(plan_materias).where(plan_materias.c.plan_id == plan_id))
    if unique_ids:
        await db.execute(
            insert(plan_materias),
            [{"plan_id": plan_id, "materia_id": mid} for mid in unique_ids],
        )
    await db.flush()
    return {"plan_id": plan_id, "materia_ids": unique_ids}


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: int,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
    plan = await db.get(PlanEstudio, plan_id)
    if plan is None or plan.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    plan.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None
