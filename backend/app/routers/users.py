from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, require_role
from app.core.roles import VALID_ROLES
from app.core.security import get_password_hash
from app.models.sede import Sede
from app.models.user import User
from app.schemas.user import TeachingUpdate, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def _validate_role(role: str) -> None:
    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=422,
            detail="Rol inválido. Usa admin, coordinador, subcoordinador, tutor o alumno.",
        )


async def _validate_sede(db: AsyncSession, sede_id: int | None) -> None:
    if sede_id is None:
        return
    sede = await db.get(Sede, sede_id)
    if sede is None or sede.deleted_at is not None:
        raise HTTPException(status_code=422, detail="La sede indicada no existe.")


async def _email_taken(db: AsyncSession, email: str, exclude_user_id: int | None = None) -> bool:
    stmt = select(User.id).where(func.lower(User.email) == email.strip().lower())
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(require_role("admin", "coordinador", "tutor"))):
    return user


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    user=Depends(require_role("admin")),
):
    _validate_role(payload.role)
    await _validate_sede(db, payload.sede_id)
    if await _email_taken(db, payload.email):
        raise HTTPException(status_code=409, detail="Email ya registrado")
    new_user = User(
        email=payload.email.strip().lower(),
        password_hash=get_password_hash(payload.password),
        nombre=payload.nombre,
        apellido_paterno=payload.apellido_paterno,
        apellido_materno=payload.apellido_materno,
        role=payload.role,
        es_tutor=payload.es_tutor,
        sede_id=payload.sede_id,
        telefono=payload.telefono,
        area_principal=payload.area_principal,
        carga_max_horas=payload.carga_max_horas,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return new_user


@router.put("/me/teaching")
async def update_teaching(
    payload: TeachingUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    if user.role not in ("admin", "coordinador", "subcoordinador"):
        raise HTTPException(status_code=403, detail="No autorizado")
    if user.role == "tutor" and not payload.enabled:
        raise HTTPException(status_code=403, detail="Los tutores deben impartir clases")
    user.es_tutor = payload.enabled
    await db.flush()
    return {"es_tutor": user.es_tutor}


@router.get("", response_model=list[UserRead])
async def list_users(
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
    sede_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    es_tutor: bool | None = Query(default=None),
    sort_by: str = Query(default="nombre"),
    sort_dir: str = Query(default="asc"),
    db: AsyncSession = Depends(get_async_db),
    user=Depends(require_role("admin")),
):
    stmt = select(User).where(User.deleted_at.is_(None))
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.nombre.ilike(term),
                User.apellido_paterno.ilike(term),
                User.apellido_materno.ilike(term),
                User.email.ilike(term),
            )
        )
    if role:
        stmt = stmt.where(User.role == role)
    if sede_id is not None:
        stmt = stmt.where(User.sede_id == sede_id)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if es_tutor is not None:
        stmt = stmt.where(User.es_tutor == es_tutor)
    sort_fields = {
        "nombre": User.nombre,
        "apellido_paterno": User.apellido_paterno,
        "email": User.email,
        "role": User.role,
        "sede_id": User.sede_id,
        "id": User.id,
    }
    sort_column = sort_fields.get(sort_by, User.nombre)
    stmt = stmt.order_by(sort_column.desc() if sort_dir.lower() == "desc" else sort_column.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    user=Depends(require_role("admin")),
):
    target = await db.get(User, user_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    changes = payload.model_dump(exclude_unset=True)
    if "role" in changes and changes["role"] is not None:
        _validate_role(changes["role"])
    if "sede_id" in changes:
        await _validate_sede(db, changes["sede_id"])
    if "email" in changes and changes["email"] is not None:
        if await _email_taken(db, str(changes["email"]), exclude_user_id=target.id):
            raise HTTPException(status_code=409, detail="Email ya registrado")
        changes["email"] = str(changes["email"]).strip().lower()
    for field, value in changes.items():
        setattr(target, field, value)
    await db.flush()
    await db.refresh(target)
    return target


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_async_db),
):
    target = await db.get(User, user_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target.deleted_at = datetime.now(timezone.utc)
    target.is_active = False
    await db.flush()
    return None
