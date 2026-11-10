from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.student import Student, Enrollment
from app.models.sede import Sede, Grupo
from app.models.materia import Materia
from app.models.corrida import CorridaHorario
from app.schemas.student import StudentRead, StudentUpdate
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentRead,
    EnrollmentStatusUpdate,
)
from app.services.email import send_email_sync
from fastapi.concurrency import run_in_threadpool

router = APIRouter(tags=["students"])

ACTIVE_STATUSES = {"confirmada", "pendiente_pago"}


async def _get_student(db: AsyncSession, user: User) -> Student:
    result = await db.execute(select(Student).where(Student.user_id == user.id))
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="Perfil de estudiante no encontrado")
    return student


async def _active_count(db: AsyncSession, grupo_id: int) -> int:
    result = await db.execute(
        select(func.count(Enrollment.id)).where(
            Enrollment.grupo_id == grupo_id,
            Enrollment.estado.in_(ACTIVE_STATUSES),
        )
    )
    return int(result.scalar() or 0)


async def _promote_waitlist(db: AsyncSession, grupo_id: int):
    # promote oldest waitlisted enrollment
    result = await db.execute(
        select(Enrollment).where(Enrollment.grupo_id == grupo_id, Enrollment.estado == "lista_espera").order_by(Enrollment.created_at)
    )
    wl = result.scalars().first()
    if wl is None:
        return
    grupo = await db.get(Grupo, grupo_id)
    sede = await db.get(Sede, grupo.sede_id) if grupo else None
    if grupo is None:
        return
    # check capacity
    if await _active_count(db, grupo_id) >= grupo.capacidad:
        return
    if sede and sede.payment_enabled:
        wl.estado = "pendiente_pago"
        wl.payment_status = "pendiente"
    else:
        wl.estado = "confirmada"
        wl.payment_status = "no_requerido"
    await db.flush()
    # notify student
    student = await db.get(Student, wl.student_id)
    if student:
        user = await db.get(User, student.user_id)
        if user:
            await run_in_threadpool(
                send_email_sync,
                user.email,
                "Promoción de lista de espera - CUEP",
                f"Has sido promovido de la lista de espera al grupo {grupo.nombre}.",
            )


@router.get("/students/me", response_model=StudentRead)
async def get_my_student(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    return await _get_student(db, user)


@router.put("/students/me", response_model=StudentRead)
async def update_my_student(payload: StudentUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    student = await _get_student(db, user)
    if payload.sede_id is not None:
        student.sede_id = payload.sede_id
    if payload.nivel is not None:
        student.nivel = payload.nivel
    if payload.area is not None:
        student.area = payload.area
    if payload.estatus is not None:
        student.estatus = payload.estatus
    await db.flush()
    await db.refresh(student)
    return student


@router.get("/groups/available")
async def available_groups(
    sede_id: int = Query(...),
    nivel: str = Query(...),
    area: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    stmt = select(Grupo).where(Grupo.sede_id == sede_id)
    result = await db.execute(stmt)
    grupos = result.scalars().all()
    out = []
    for g in grupos:
        materia = await db.get(Materia, g.materia_id)
        if materia is None or materia.nivel != nivel:
            continue
        if nivel == "LICENCIATURA" and area and materia.area != area:
            continue
        count = await _active_count(db, g.id)
        out.append({
            "id": g.id,
            "nombre": g.nombre,
            "materia": materia.nombre,
            "nivel": materia.nivel,
            "area": materia.area,
            "capacidad": g.capacidad,
            "ocupados": count,
            "disponibles": max(g.capacidad - count, 0),
            "min_alumnos": g.min_alumnos,
        })
    return out


@router.post("/enrollments", response_model=EnrollmentRead, status_code=201)
async def create_enrollment(payload: EnrollmentCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    student = await _get_student(db, user)
    grupo = await db.get(Grupo, payload.grupo_id)
    if grupo is None:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
    if grupo.sede_id != student.sede_id:
        raise HTTPException(status_code=400, detail="El grupo no pertenece a tu sede")
    materia = await db.get(Materia, grupo.materia_id)
    if materia is None or materia.nivel != student.nivel:
        raise HTTPException(status_code=400, detail="Nivel incompatible")
    if student.nivel == "LICENCIATURA" and student.area and materia.area != student.area:
        raise HTTPException(status_code=400, detail="Área incompatible")
    sede = await db.get(Sede, grupo.sede_id)
    # duplicate check
    dup = await db.execute(select(Enrollment).where(Enrollment.student_id == student.id, Enrollment.grupo_id == grupo.id, Enrollment.estado != "cancelada"))
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya estás inscrito en este grupo")
    occupied = await _active_count(db, grupo.id)
    if occupied >= grupo.capacidad:
        if sede and sede.waitlist_enabled:
            enrollment = Enrollment(student_id=student.id, grupo_id=grupo.id, estado="lista_espera", payment_status="no_requerido")
            db.add(enrollment)
            await db.flush()
            await db.refresh(enrollment)
            return enrollment
        raise HTTPException(status_code=409, detail="Grupo sin cupo")
    if sede and sede.payment_enabled:
        enrollment = Enrollment(student_id=student.id, grupo_id=grupo.id, estado="pendiente_pago", payment_status="pendiente")
    else:
        enrollment = Enrollment(student_id=student.id, grupo_id=grupo.id, estado="confirmada", payment_status="no_requerido")
    db.add(enrollment)
    await db.flush()
    await db.refresh(enrollment)
    # notify
    await run_in_threadpool(send_email_sync, user.email, "Inscripción CUEP", f"Tu inscripción al grupo {grupo.nombre} está {enrollment.estado}.")
    return enrollment


@router.get("/enrollments/me", response_model=list[EnrollmentRead])
async def my_enrollments(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    student = await _get_student(db, user)
    result = await db.execute(select(Enrollment).where(Enrollment.student_id == student.id))
    return result.scalars().all()


@router.delete("/enrollments/{enrollment_id}", status_code=204)
async def cancel_enrollment(enrollment_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    student = await _get_student(db, user)
    enrollment = await db.get(Enrollment, enrollment_id)
    if enrollment is None or enrollment.student_id != student.id:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    if enrollment.estado == "cancelada":
        return None
    was_active = enrollment.estado in ACTIVE_STATUSES
    enrollment.estado = "cancelada"
    enrollment.updated_at = datetime.utcnow()
    await db.flush()
    if was_active:
        await _promote_waitlist(db, enrollment.grupo_id)
    return None


@router.get("/students/me/schedule")
async def my_schedule(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    student = await _get_student(db, user)
    result = await db.execute(select(Enrollment).where(Enrollment.student_id == student.id, Enrollment.estado.in_(ACTIVE_STATUSES)))
    enrollments = result.scalars().all()
    out = []
    for e in enrollments:
        grupo = await db.get(Grupo, e.grupo_id)
        if grupo is None:
            continue
        materia = await db.get(Materia, grupo.materia_id)
        # find latest completed corrida containing this group
        corridas = await db.execute(select(CorridaHorario).where(CorridaHorario.estado == "COMPLETADO", CorridaHorario.publicada == True))  # noqa: E712
        tutor_id = None
        slot = None
        for c in corridas.scalars().all():
            params = c.parametros_resumen or {}
            grupo_ids = [g.get("id") for g in params.get("grupos", [])]
            if grupo.id not in grupo_ids:
                continue
            res = c.resultado_json or {}
            for a in res.get("asignaciones", []):
                if a.get("grupo_id") == grupo.id:
                    tutor_id = a.get("tutor_id")
                    slot = {"dia": a.get("dia"), "hora_inicio": a.get("hora_inicio"), "hora_fin": a.get("hora_fin")}
        tutor = await db.get(User, tutor_id) if tutor_id else None
        out.append({
            "grupo_id": grupo.id,
            "grupo": grupo.nombre,
            "materia": materia.nombre if materia else None,
            "tutor": f"{tutor.nombre} {tutor.apellido_paterno}" if tutor else None,
            "horario": slot,
        })
    return out


# Admin endpoints
@router.get("/enrollments", response_model=list[EnrollmentRead])
async def list_enrollments(grupo_id: int | None = None, estado: str | None = None, user: User = Depends(require_role("admin", "coordinador")), db: AsyncSession = Depends(get_async_db)):
    stmt = select(Enrollment)
    if grupo_id:
        stmt = stmt.where(Enrollment.grupo_id == grupo_id)
    if estado:
        stmt = stmt.where(Enrollment.estado == estado)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentRead)
async def update_enrollment(enrollment_id: int, payload: EnrollmentStatusUpdate, user: User = Depends(require_role("admin", "coordinador")), db: AsyncSession = Depends(get_async_db)):
    enrollment = await db.get(Enrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    if payload.estado is not None:
        enrollment.estado = payload.estado
    if payload.payment_status is not None:
        enrollment.payment_status = payload.payment_status
        if payload.payment_status == "pagado" and enrollment.estado == "pendiente_pago":
            enrollment.estado = "confirmada"
            await _promote_waitlist(db, enrollment.grupo_id)
    await db.flush()
    await db.refresh(enrollment)
    # notify student on confirmation
    student = await db.get(Student, enrollment.student_id)
    if student:
        u = await db.get(User, student.user_id)
        if u:
            await run_in_threadpool(send_email_sync, u.email, "Estado de inscripción CUEP", f"Tu inscripción ahora está {enrollment.estado}.")
    return enrollment


