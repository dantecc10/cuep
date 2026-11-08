from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
from app.core.dependencies import require_role
from app.models.sede import Sede, Grupo
from app.models.user import User
from app.schemas.sede import SedeCreate, SedeRead, GrupoCreate, GrupoRead

router = APIRouter(prefix="/sedes", tags=["sedes"])


@router.get("", response_model=list[SedeRead])
async def list_sedes(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Sede))
    return result.scalars().all()


@router.post("", response_model=SedeRead, status_code=201)
async def create_sede(payload: SedeCreate, db: AsyncSession = Depends(get_async_db), user: User = Depends(require_role("admin", "coordinador"))):
    sede = Sede(**payload.model_dump())
    db.add(sede)
    await db.flush()
    await db.refresh(sede)
    return sede


@router.get("/{sede_id}/grupos", response_model=list[GrupoRead])
async def list_grupos(sede_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Grupo).where(Grupo.sede_id == sede_id))
    return result.scalars().all()


@router.post("/{sede_id}/grupos", response_model=GrupoRead, status_code=201)
async def create_grupo(sede_id: int, payload: GrupoCreate, db: AsyncSession = Depends(get_async_db), user: User = Depends(require_role("admin", "coordinador"))):
    grupo = Grupo(sede_id=sede_id, **payload.model_dump())
    db.add(grupo)
    await db.flush()
    await db.refresh(grupo)
    return grupo
