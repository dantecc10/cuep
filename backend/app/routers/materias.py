from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
from app.core.dependencies import require_role
from app.models.materia import Materia
from app.schemas.materia import MateriaCreate, MateriaRead
from app.models.user import User

router = APIRouter(prefix="/materias", tags=["materias"])


@router.get("", response_model=list[MateriaRead])
async def list_materias(nivel: str | None = None, area: str | None = None, db: AsyncSession = Depends(get_async_db)):
    stmt = select(Materia)
    if nivel:
        stmt = stmt.where(Materia.nivel == nivel)
    if area:
        stmt = stmt.where(Materia.area == area)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=MateriaRead, status_code=201)
async def create_materia(payload: MateriaCreate, db: AsyncSession = Depends(get_async_db), user: User = Depends(require_role("admin"))):
    materia = Materia(**payload.model_dump())
    db.add(materia)
    await db.flush()
    await db.refresh(materia)
    return materia
