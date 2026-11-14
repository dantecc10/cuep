from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.core.database import get_async_db
from app.core.dependencies import can_manage_sede, get_current_user, require_role
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
from app.services.grupos import (
    GrupoError,
    asignar_grupo,
    notificar_estado_inscripcion,
    notificar_promocion,
)
from app.services.normalization import normalize_phone_mx

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
    student = await db.get(Student, wl.student_id)
    if student:
        materia = await db.get(Materia, grupo.materia_id)
        if materia:
            await notificar_promocion(db, student, sede, grupo, materia)


@router.get("/students/me", response_model=StudentRead)
async def get_my_student(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    return await _get_student(db, user)


@router.put("/students/me", response_model=StudentRead)
async def update_my_student(payload: StudentUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    student = await _get_student(db, user)
    for field in ["preferred_sede_id", "first_name", "paternal_last_name", "maternal_last_name", "full_name", "address", "colony", "municipality_state", "emergency_contact_raw", "emergency_contact_name", "emergency_contact_phone", "high_school_type", "exam_attempts", "desired_degree", "study_area", "diagnostic_exam", "donation_willingness", "presencial_consent", "preferred_course_location", "photo_url", "notes"]:
        value = getattr(payload, field, None)
        if value is not None:
            setattr(student, field, value)
    if payload.phone is not None:
        try:
            phone_normalized = normalize_phone_mx(payload.phone)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        duplicate = await db.execute(
            select(Student.id).where(
                Student.phone_normalized == phone_normalized,
                Student.id != student.id,
                Student.deleted_at.is_(None),
            ).limit(1)
        )
        if duplicate.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Teléfono ya registrado")
        student.phone = payload.phone
        student.phone_normalized = phone_normalized
        user.telefono = payload.phone
    if payload.photo_url is not None:
        user.foto_url = payload.photo_url
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
    if user.role not in ("admin", "coordinador", "subcoordinador"):
        raise HTTPException(status_code=403, detail="Sólo el personal puede asignar grupos")
    if payload.student_id is None:
        raise HTTPException(status_code=422, detail="Selecciona al alumno a inscribir")
    student = await db.get(Student, payload.student_id)
    if student is None or student.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Perfil de estudiante no encontrado")
    if not can_manage_sede(user, student.sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    try:
        resultado = await asignar_grupo(db, student, payload.grupo_id, actor_id=user.id)
    except GrupoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return resultado["enrollment"]


async def _enrollment_detail(db: AsyncSession, enrollment: Enrollment) -> dict:
    student = await db.get(Student, enrollment.student_id)
    grupo = await db.get(Grupo, enrollment.grupo_id)
    materia = await db.get(Materia, grupo.materia_id) if grupo else None
    student_name = None
    if student:
        student_name = (
            " ".join(
                part
                for part in [student.first_name, student.paternal_last_name, student.maternal_last_name]
                if part
            )
            or student.full_name
            or student.email
        )
    return {
        "id": enrollment.id,
        "student_id": enrollment.student_id,
        "grupo_id": enrollment.grupo_id,
        "estado": enrollment.estado,
        "payment_status": enrollment.payment_status,
        "student_name": student_name,
        "student_matricula": student.matricula if student else None,
        "grupo_name": grupo.nombre if grupo else None,
        "materia_name": materia.nombre if materia else None,
    }


@router.get("/enrollments/me", response_model=list[EnrollmentRead])
async def my_enrollments(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    student = await _get_student(db, user)
    result = await db.execute(select(Enrollment).where(Enrollment.student_id == student.id))
    return [await _enrollment_detail(db, enrollment) for enrollment in result.scalars().all()]


@router.delete("/enrollments/{enrollment_id}", status_code=204)
async def cancel_enrollment(enrollment_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if user.role not in ("admin", "coordinador", "subcoordinador"):
        raise HTTPException(status_code=403, detail="Sólo el personal puede cancelar grupos")
    enrollment = await db.get(Enrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    student = await db.get(Student, enrollment.student_id)
    if student is None or not can_manage_sede(user, student.sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
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
    return [await _enrollment_detail(db, enrollment) for enrollment in result.scalars().all()]


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
    student = await db.get(Student, enrollment.student_id)
    if student:
        grupo = await db.get(Grupo, enrollment.grupo_id)
        if grupo:
            materia = await db.get(Materia, grupo.materia_id)
            sede = await db.get(Sede, grupo.sede_id)
            if materia:
                await notificar_estado_inscripcion(
                    db, student, grupo, materia, sede, enrollment.estado
                )
    return enrollment


