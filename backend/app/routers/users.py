from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import require_role, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, TeachingUpdate, UserUpdate
from app.core.security import get_password_hash

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(require_role("admin", "coordinador", "tutor"))):
    return user


@router.post("", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_async_db), user=Depends(require_role("admin"))):
    new_user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        nombre=payload.nombre,
        apellido_paterno=payload.apellido_paterno,
        apellido_materno=payload.apellido_materno,
        role=payload.role,
        es_tutor=payload.es_tutor,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return new_user


@router.put("/me/teaching")
async def update_teaching(payload: TeachingUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if user.role not in ("admin", "coordinador", "subcoordinador"):
        raise HTTPException(status_code=403, detail="No autorizado")
    if user.role == "tutor" and not payload.enabled:
        raise HTTPException(status_code=403, detail="Los tutores deben impartir clases")
    user.es_tutor = payload.enabled
    await db.flush()
    return {"es_tutor": user.es_tutor}


@router.get("", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_async_db), user=Depends(require_role("admin"))):
    result = await db.execute(select(User).where(User.deleted_at.is_(None)))
    return result.scalars().all()


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_async_db), user=Depends(require_role("admin"))):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(target, field, value)
    await db.flush()
    await db.refresh(target)
    return target


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, user: User = Depends(require_role("admin")), db: AsyncSession = Depends(get_async_db)):
    target = await db.get(User, user_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target.deleted_at = datetime.now(timezone.utc)
    target.is_active = False
    await db.flush()
    return None
