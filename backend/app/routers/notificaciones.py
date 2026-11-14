from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import require_role
from app.models.notificacion import NotificacionOutbox, NotificacionPlantilla
from app.models.sede import Sede
from app.models.student import Student
from app.models.user import User
from app.schemas.notificacion import (
    EnviarNotificacion,
    OutboxPage,
    OutboxRead,
    PlantillaRead,
    PlantillaUpdate,
)
from app.services.notificaciones import (
    enqueue_notificacion,
    send_pending_notificaciones,
    student_context,
)

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.get("/plantillas", response_model=list[PlantillaRead])
async def list_plantillas(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(select(NotificacionPlantilla).order_by(NotificacionPlantilla.clave))
    return result.scalars().all()


@router.put("/plantillas/{clave}", response_model=PlantillaRead)
async def update_plantilla(
    clave: str,
    payload: PlantillaUpdate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin")),
):
    result = await db.execute(
        select(NotificacionPlantilla).where(NotificacionPlantilla.clave == clave)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    await db.flush()
    await db.refresh(template)
    return template


@router.get("/outbox", response_model=OutboxPage)
async def list_outbox(
    estado: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin")),
):
    stmt = select(NotificacionOutbox)
    if estado:
        stmt = stmt.where(NotificacionOutbox.estado == estado)
    total = await db.execute(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(
        stmt.order_by(NotificacionOutbox.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return OutboxPage(
        items=result.scalars().all(),
        total=int(total.scalar_one()),
        page=page,
        page_size=page_size,
    )


@router.post("/enviar", response_model=OutboxRead, status_code=201)
async def enviar_notificacion(
    payload: EnviarNotificacion,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin", "coordinador")),
):
    student = await db.get(Student, payload.student_id)
    if student is None or student.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    if user.role != "admin" and user.sede_id != student.sede_id:
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    if not student.email:
        raise HTTPException(status_code=422, detail="El alumno no tiene correo registrado")
    sede = await db.get(Sede, student.sede_id) if student.sede_id else None
    context = student_context(student, sede)
    context.update({key: str(value) for key, value in (payload.contexto or {}).items()})
    outbox = await enqueue_notificacion(
        db,
        payload.clave,
        student,
        student.email,
        context=context,
        dedupe_key=payload.dedupe_key,
    )
    if outbox is None:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada o inactiva")
    return outbox


@router.post("/outbox/{outbox_id}/reintentar", response_model=OutboxRead)
async def reintentar(
    outbox_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin")),
):
    outbox = await db.get(NotificacionOutbox, outbox_id)
    if outbox is None:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if outbox.estado == "enviado":
        raise HTTPException(status_code=409, detail="La notificación ya fue enviada")
    outbox.estado = "pendiente"
    outbox.programado_para = datetime.now(timezone.utc)
    outbox.ultimo_error = None
    await db.flush()
    await db.refresh(outbox)
    return outbox


@router.post("/procesar")
async def procesar_outbox(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin")),
):
    return await send_pending_notificaciones(db, limit)
