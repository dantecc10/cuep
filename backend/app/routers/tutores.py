from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, or_, select
from app.core.database import get_async_db
from app.core.dependencies import can_manage_sede, require_role, get_current_user
from app.models.user import User
from app.models.corrida import CorridaHorario
from app.models.sede import Grupo
from app.models.materia import Materia
from app.models.disponibilidad import DisponibilidadTutor, TutorMateria
from app.schemas.tutor import TutorUpdate
from app.services.horario import cargar_horario
from app.schemas.user import UserRead

router = APIRouter(prefix="/tutores", tags=["tutores"])


@router.get("", response_model=list[UserRead])
async def list_tutores(
    search: str | None = None,
    sede_id: int | None = None,
    sort_by: str = "nombre",
    sort_dir: str = "asc",
    db: AsyncSession = Depends(get_async_db),
    user=Depends(require_role("admin", "coordinador", "subcoordinador")),
):
    stmt = select(User).where(User.es_tutor.is_(True), User.deleted_at.is_(None))
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
    if sede_id is not None:
        stmt = stmt.where(User.sede_id == sede_id)
    sort_fields = {
        "nombre": User.nombre,
        "apellido_paterno": User.apellido_paterno,
        "email": User.email,
        "sede_id": User.sede_id,
        "id": User.id,
    }
    sort_column = sort_fields.get(sort_by, User.nombre)
    stmt = stmt.order_by(sort_column.desc() if sort_dir.lower() == "desc" else sort_column.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{tutor_id}", response_model=UserRead)
async def get_tutor(tutor_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.id == tutor_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Tutor no encontrado")
    return user


async def _get_tutor_or_404(db: AsyncSession, tutor_id: int) -> User:
    target = await db.get(User, tutor_id)
    if target is None or target.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tutor no encontrado")
    return target


def _authorize_tutor_config(user: User, target: User) -> None:
    if user.id != target.id and not can_manage_sede(user, target.sede_id):
        raise HTTPException(status_code=403, detail="No autorizado")


async def _validate_disponibilidad(db: AsyncSession, rows) -> None:
    horario = {row.dia_semana: row for row in await cargar_horario(db)}
    by_day: dict[int, list] = {}
    for item in rows:
        if item.dia_semana < 1 or item.dia_semana > 7:
            raise HTTPException(status_code=422, detail="Día de la semana inválido")
        if item.hora_inicio >= item.hora_fin:
            raise HTTPException(status_code=422, detail="La hora de inicio debe ser anterior a la de fin")
        if item.hora_inicio.minute or item.hora_inicio.second or item.hora_fin.minute or item.hora_fin.second:
            raise HTTPException(status_code=422, detail="La disponibilidad debe ser en horas completas")
        config = horario.get(item.dia_semana)
        if config is None or not config.activo:
            raise HTTPException(status_code=422, detail="Ese día no está habilitado en el horario del CUEP")
        if item.hora_inicio < config.hora_inicio or item.hora_fin > config.hora_fin:
            raise HTTPException(status_code=422, detail="La disponibilidad debe estar dentro del horario del CUEP")
        by_day.setdefault(item.dia_semana, []).append(item)
    for day, items in by_day.items():
        ordered = sorted(items, key=lambda item: item.hora_inicio)
        for previous, current in zip(ordered, ordered[1:]):
            if current.hora_inicio < previous.hora_fin:
                raise HTTPException(status_code=422, detail=f"Hay bloques traslapados el día {day}")


@router.get("/{tutor_id}/disponibilidad")
async def get_disponibilidad(tutor_id: int, db: AsyncSession = Depends(get_async_db), user=Depends(get_current_user)):
    target = await _get_tutor_or_404(db, tutor_id)
    _authorize_tutor_config(user, target)
    disp_result = await db.execute(
        select(DisponibilidadTutor)
        .where(DisponibilidadTutor.tutor_id == tutor_id)
        .order_by(DisponibilidadTutor.dia_semana, DisponibilidadTutor.hora_inicio)
    )
    materias_result = await db.execute(select(TutorMateria).where(TutorMateria.tutor_id == tutor_id))
    return {
        "disponibilidad": [
            {
                "dia_semana": item.dia_semana,
                "hora_inicio": item.hora_inicio.strftime("%H:%M"),
                "hora_fin": item.hora_fin.strftime("%H:%M"),
            }
            for item in disp_result.scalars().all()
        ],
        "materias": [
            {
                "materia_id": item.materia_id,
                "nivel_preferencia": item.nivel_preferencia,
                "vetada": item.vetada,
            }
            for item in materias_result.scalars().all()
        ],
        "carga_max_horas": target.carga_max_horas,
        "area_principal": target.area_principal,
    }


@router.put("/{tutor_id}/disponibilidad", status_code=204)
async def update_disponibilidad(tutor_id: int, payload: TutorUpdate, db: AsyncSession = Depends(get_async_db), user=Depends(get_current_user)):
    target = await _get_tutor_or_404(db, tutor_id)
    _authorize_tutor_config(user, target)
    if payload.disponibilidad is not None:
        await _validate_disponibilidad(db, payload.disponibilidad)
        await db.execute(delete(DisponibilidadTutor).where(DisponibilidadTutor.tutor_id == tutor_id))
        for d in payload.disponibilidad:
            db.add(DisponibilidadTutor(tutor_id=tutor_id, dia_semana=d.dia_semana, hora_inicio=d.hora_inicio, hora_fin=d.hora_fin))
    if payload.materias is not None:
        await db.execute(delete(TutorMateria).where(TutorMateria.tutor_id == tutor_id))
        for m in payload.materias:
            db.add(TutorMateria(tutor_id=tutor_id, materia_id=m.materia_id, nivel_preferencia=m.nivel_preferencia))
    if payload.carga_max_horas is not None:
        target = await db.get(User, tutor_id)
        if target:
            target.carga_max_horas = payload.carga_max_horas
    if payload.area_principal is not None:
        target = await db.get(User, tutor_id)
        if target:
            target.area_principal = payload.area_principal
    await db.flush()
    return None


@router.get("/me/horario")
async def my_tutor_schedule(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if not user.es_tutor:
        raise HTTPException(status_code=403, detail="El usuario no es tutor")
    result = await db.execute(select(CorridaHorario).where(CorridaHorario.publicada == True))  # noqa: E712
    out = []
    for c in result.scalars().all():
        res = c.resultado_json or {}
        for a in res.get("asignaciones", []):
            if a.get("tutor_id") != user.id:
                continue
            grupo = await db.get(Grupo, a.get("grupo_id"))
            materia = await db.get(Materia, grupo.materia_id) if grupo else None
            out.append({
                "corrida_id": c.id,
                "grupo_id": a.get("grupo_id"),
                "grupo": grupo.nombre if grupo else None,
                "materia": materia.nombre if materia else None,
                "dia": a.get("dia"),
                "hora_inicio": a.get("hora_inicio"),
                "hora_fin": a.get("hora_fin"),
            })
    return out
