from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import require_role
from app.models.materia import Materia
from app.models.plan import PlanEstudio, plan_materias
from app.models.user import User
from app.schemas.materia import MateriaCreate, MateriaRead

router = APIRouter(prefix="/materias", tags=["materias"])


SORT_FIELDS = {
    "nombre": Materia.nombre,
    "nivel": Materia.nivel,
    "area": Materia.area,
    "id": Materia.id,
}


@router.get("", response_model=list[MateriaRead])
async def list_materias(
    nivel: str | None = None,
    area: str | None = None,
    search: str | None = Query(default=None),
    sort_by: str = Query(default="nombre"),
    sort_dir: str = Query(default="asc"),
    db: AsyncSession = Depends(get_async_db),
):
    stmt = select(Materia).where(Materia.deleted_at.is_(None))
    if nivel:
        stmt = stmt.where(Materia.nivel == nivel)
    if area:
        stmt = stmt.where(Materia.area == area)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Materia.nombre.ilike(term),
                Materia.area.ilike(term),
                Materia.descripcion.ilike(term),
            )
        )
    sort_column = SORT_FIELDS.get(sort_by, Materia.nombre)
    stmt = stmt.order_by(sort_column.desc() if sort_dir.lower() == "desc" else sort_column.asc())
    result = await db.execute(stmt)
    materias = list(result.scalars().all())
    counts_result = await db.execute(
        select(plan_materias.c.materia_id, func.count(plan_materias.c.plan_id))
        .join(PlanEstudio, PlanEstudio.id == plan_materias.c.plan_id)
        .where(PlanEstudio.deleted_at.is_(None))
        .group_by(plan_materias.c.materia_id)
    )
    counts = dict(counts_result.all())
    for materia in materias:
        materia.planes_count = counts.get(materia.id, 0)
    return materias


@router.post("", response_model=MateriaRead, status_code=201)
async def create_materia(
    payload: MateriaCreate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin")),
):
    materia = Materia(**payload.model_dump())
    db.add(materia)
    await db.flush()
    await db.refresh(materia)
    return materia


@router.put("/{materia_id}", response_model=MateriaRead)
async def update_materia(
    materia_id: int,
    payload: MateriaCreate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
    materia = await db.get(Materia, materia_id)
    if materia is None or materia.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    materia.nombre = payload.nombre
    materia.nivel = payload.nivel
    materia.area = payload.area
    materia.descripcion = payload.descripcion
    await db.flush()
    await db.refresh(materia)
    return materia


@router.delete("/{materia_id}", status_code=204)
async def delete_materia(
    materia_id: int,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
    materia = await db.get(Materia, materia_id)
    if materia is None or materia.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    await db.execute(delete(plan_materias).where(plan_materias.c.materia_id == materia_id))
    materia.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    return None
