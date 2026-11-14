from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inscripcion import EventoInscripcion
from app.models.materia import Materia
from app.models.sede import Grupo, Sede
from app.models.student import Enrollment, Student
from app.models.user import User
from app.services.notificaciones import enqueue_notificacion, student_context


class GrupoError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def _ocupados(db: AsyncSession, grupo_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Enrollment)
        .where(
            Enrollment.grupo_id == grupo_id,
            Enrollment.estado.notin_(("cancelada", "lista_espera")),
            Enrollment.deleted_at.is_(None),
        )
    )
    return int(result.scalar_one())


async def _grupo_y_materia(db: AsyncSession, grupo_id: int) -> tuple[Grupo, Materia]:
    grupo = await db.get(Grupo, grupo_id)
    if grupo is None:
        raise GrupoError("Grupo no encontrado", 404)
    materia = await db.get(Materia, grupo.materia_id)
    if materia is None:
        raise GrupoError("El grupo no tiene materia asignada", 400)
    return grupo, materia


def _validar_compatibilidad(student: Student, grupo: Grupo, materia: Materia) -> None:
    if grupo.sede_id != student.sede_id:
        raise GrupoError("El grupo no pertenece a la sede del alumno", 400)
    if materia.nivel != student.nivel:
        raise GrupoError("Nivel incompatible", 400)
    if student.nivel == "LICENCIATURA" and student.area and materia.area != student.area:
        raise GrupoError("Área incompatible", 400)


async def asignar_grupo(
    db: AsyncSession,
    student: Student,
    grupo_id: int,
    actor_id: int | None = None,
) -> dict:
    """Asigna un grupo a un alumno y deja el evento en la bitácora."""
    if student.estatus in ("cancelado", "baja"):
        raise GrupoError("La inscripción está cancelada o de baja", 409)

    grupo, materia = await _grupo_y_materia(db, grupo_id)
    _validar_compatibilidad(student, grupo, materia)

    duplicado = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.grupo_id == grupo.id,
            Enrollment.estado != "cancelada",
            Enrollment.deleted_at.is_(None),
        )
    )
    if duplicado.scalar_one_or_none() is not None:
        raise GrupoError("El alumno ya está en este grupo", 409)

    sede = await db.get(Sede, grupo.sede_id)
    ocupados = await _ocupados(db, grupo.id)
    if ocupados >= grupo.capacidad:
        if not (sede and sede.waitlist_enabled):
            raise GrupoError("El grupo no tiene cupo", 409)
        enrollment = Enrollment(
            student_id=student.id,
            grupo_id=grupo.id,
            estado="lista_espera",
            payment_status="no_requerido",
        )
    elif sede and sede.payment_enabled:
        enrollment = Enrollment(
            student_id=student.id,
            grupo_id=grupo.id,
            estado="pendiente_pago",
            payment_status="pendiente",
        )
    else:
        enrollment = Enrollment(
            student_id=student.id,
            grupo_id=grupo.id,
            estado="confirmada",
            payment_status="no_requerido",
        )

    db.add(enrollment)
    await db.flush()
    await db.refresh(enrollment)

    db.add(
        EventoInscripcion(
            student_id=student.id,
            tipo="asignacion_grupo",
            estado_nuevo=enrollment.estado,
            actor_id=actor_id,
            sede_id=grupo.sede_id,
            detalle={
                "grupo_id": grupo.id,
                "grupo": grupo.nombre,
                "materia": materia.nombre,
                "estado": enrollment.estado,
            },
        )
    )
    await db.flush()

    await _notificar(
        db,
        student,
        sede,
        grupo,
        materia,
        enrollment.estado,
        clave="grupo_asignado",
    )
    return {
        "enrollment": enrollment,
        "grupo": grupo,
        "materia": materia,
        "sede": sede,
    }


async def desasignar_grupo(
    db: AsyncSession,
    student: Student,
    enrollment: Enrollment,
    actor_id: int | None = None,
) -> None:
    if enrollment.student_id != student.id:
        raise GrupoError("El grupo no pertenece a este alumno", 404)
    enrollment.estado = "cancelada"
    enrollment.deleted_at = datetime.now(timezone.utc)
    db.add(
        EventoInscripcion(
            student_id=student.id,
            tipo="asignacion_grupo",
            estado_anterior="confirmada",
            estado_nuevo="cancelada",
            actor_id=actor_id,
            sede_id=student.sede_id,
            detalle={"grupo_id": enrollment.grupo_id, "accion": "desasignacion"},
        )
    )
    await db.flush()


async def grupos_del_alumno(db: AsyncSession, student: Student) -> list[dict]:
    result = await db.execute(
        select(Enrollment)
        .where(
            Enrollment.student_id == student.id,
            Enrollment.deleted_at.is_(None),
        )
        .order_by(Enrollment.created_at.desc())
    )
    enrollments = result.scalars().all()
    grupos: list[dict] = []
    for enrollment in enrollments:
        grupo = await db.get(Grupo, enrollment.grupo_id)
        materia = await db.get(Materia, grupo.materia_id) if grupo else None
        sede = await db.get(Sede, grupo.sede_id) if grupo else None
        grupos.append(
            {
                "enrollment_id": enrollment.id,
                "grupo_id": enrollment.grupo_id,
                "grupo_nombre": grupo.nombre if grupo else "",
                "materia": materia.nombre if materia else None,
                "nivel": materia.nivel if materia else None,
                "area": materia.area if materia else None,
                "sede_nombre": sede.nombre if sede else None,
                "estado": enrollment.estado,
                "payment_status": enrollment.payment_status,
                "created_at": enrollment.created_at,
            }
        )
    return grupos


async def _notificar(
    db: AsyncSession,
    student: Student,
    sede: Sede | None,
    grupo: Grupo,
    materia: Materia,
    estado: str,
    clave: str,
) -> None:
    if not student.email:
        return
    context = student_context(student, sede)
    context.update(
        {
            "grupo": grupo.nombre,
            "materia": materia.nombre,
            "estado": estado,
        }
    )
    await enqueue_notificacion(
        db,
        clave,
        student,
        student.email,
        context=context,
        dedupe_key=f"{clave}:{student.id}:{grupo.id}",
    )


async def notificar_estado_inscripcion(
    db: AsyncSession,
    student: Student,
    grupo: Grupo,
    materia: Materia,
    sede: Sede | None,
    estado: str,
) -> None:
    await _notificar(db, student, sede, grupo, materia, estado, clave="estado_inscripcion")


async def notificar_promocion(
    db: AsyncSession,
    student: Student,
    sede: Sede | None,
    grupo: Grupo,
    materia: Materia,
) -> None:
    await _notificar(
        db,
        student,
        sede,
        grupo,
        materia,
        estado="confirmada",
        clave="promocion_lista_espera",
    )


async def usuario_del_alumno(db: AsyncSession, student: Student) -> User | None:
    if student.user_id is None:
        return None
    return await db.get(User, student.user_id)
