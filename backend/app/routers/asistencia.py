from collections import defaultdict
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.core.dependencies import can_manage_sede, get_current_user
from app.models.asistencia import ESTADOS_ASISTENCIA, SesionClase
from app.models.corrida import CorridaHorario
from app.models.materia import Materia
from app.models.sede import Grupo, Sede
from app.models.user import User
from app.schemas.asistencia import SesionCreate, SesionUpdate

router = APIRouter(prefix="/asistencia", tags=["asistencia"])

MANAGER_ROLES = ("admin", "coordinador", "subcoordinador")


def _full_name(user: User | None) -> str:
    if user is None:
        return "Sin asignar"
    return f"{user.nombre} {user.apellido_paterno} {user.apellido_materno or ''}".strip()


def _today() -> date:
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()


def _require_manager(user: User):
    if user.role not in MANAGER_ROLES:
        raise HTTPException(status_code=403, detail="Rol no autorizado")


def _sede_scope(user: User, sede_id: int | None, requested_sede_id: int | None = None) -> list[int] | None:
    if user.role == "admin":
        return [requested_sede_id] if requested_sede_id is not None else None
    if user.sede_id is None:
        raise HTTPException(status_code=403, detail="Usuario sin sede asignada")
    if requested_sede_id is not None and requested_sede_id != user.sede_id:
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    return [user.sede_id]


def _validate_estado(estado: str):
    if estado not in ESTADOS_ASISTENCIA:
        raise HTTPException(status_code=400, detail="Estado de asistencia inválido")


def _validate_cubierta(estado: str, tutor_id: int, cubridor_id: int | None):
    if estado != "cubierta":
        if cubridor_id is not None:
            raise HTTPException(status_code=400, detail="Solo las clases cubiertas pueden tener tutor cubridor")
        return
    if cubridor_id is None:
        raise HTTPException(status_code=400, detail="Una clase cubierta requiere tutor cubridor")
    if cubridor_id == tutor_id:
        raise HTTPException(status_code=400, detail="El tutor cubridor debe ser distinto al titular")


async def _load_names(db: AsyncSession, group_ids: set[int], user_ids: set[int], sede_ids: set[int]):
    groups = {}
    materias = {}
    sedes = {}
    users = {}
    if group_ids:
        groups = {g.id: g for g in (await db.execute(select(Grupo).where(Grupo.id.in_(group_ids)))).scalars().all()}
        materia_ids = {g.materia_id for g in groups.values()}
        if materia_ids:
            materias = {m.id: m for m in (await db.execute(select(Materia).where(Materia.id.in_(materia_ids)))).scalars().all()}
    if user_ids:
        users = {u.id: u for u in (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()}
    if sede_ids:
        sedes = {s.id: s for s in (await db.execute(select(Sede).where(Sede.id.in_(sede_ids)))).scalars().all()}
    return groups, materias, sedes, users


def _serialize(
    *,
    session_id: int | None,
    corrida_id: int | None,
    sede_id: int,
    grupo_id: int,
    tutor_id: int,
    fecha: date,
    dia_semana: int,
    hora_inicio,
    hora_fin,
    estado: str,
    tutor_cubridor_id: int | None,
    comentario: str | None,
    origen: str,
    registrado_por: int | None = None,
    actualizado_por: int | None = None,
    groups,
    materias,
    sedes,
    users,
    current_user: User | None = None,
):
    group = groups.get(grupo_id)
    sede = sedes.get(sede_id)
    materia = materias.get(group.materia_id) if group else None
    tutor = users.get(tutor_id)
    cubridor = users.get(tutor_cubridor_id) if tutor_cubridor_id else None
    data = {
        "id": session_id,
        "corrida_id": corrida_id,
        "sede_id": sede_id,
        "sede_nombre": sede.nombre if sede else f"Sede {sede_id}",
        "grupo_id": grupo_id,
        "grupo_nombre": group.nombre if group else f"Grupo {grupo_id}",
        "materia_nombre": materia.nombre if materia else "",
        "tutor_id": tutor_id,
        "tutor_nombre": _full_name(tutor),
        "fecha": fecha,
        "dia_semana": dia_semana,
        "hora_inicio": hora_inicio.strftime("%H:%M") if hasattr(hora_inicio, "strftime") else str(hora_inicio),
        "hora_fin": hora_fin.strftime("%H:%M") if hasattr(hora_fin, "strftime") else str(hora_fin),
        "estado": estado,
        "tutor_cubridor_id": tutor_cubridor_id,
        "tutor_cubridor_nombre": _full_name(cubridor) if cubridor else None,
        "comentario": comentario,
        "origen": origen,
        "registrado_por": registrado_por,
        "actualizado_por": actualizado_por,
    }
    if current_user is not None:
        data["rol"] = "cubridor" if (tutor_cubridor_id == current_user.id and estado == "cubierta") else "titular"
        data["impartida_por_mi"] = (
            (tutor_id == current_user.id and estado in ("asistio", "retardo"))
            or (tutor_cubridor_id == current_user.id and estado == "cubierta")
        )
    return data


@router.get("/clases")
async def listar_clases(
    fecha: date | None = None,
    sede_id: int | None = None,
    tutor_id: int | None = None,
    estado: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    _require_manager(user)
    if estado is not None:
        _validate_estado(estado)
    day = fecha or _today()
    sede_ids = _sede_scope(user, user.sede_id, sede_id)

    stmt = select(CorridaHorario).where(
        CorridaHorario.publicada == True,  # noqa: E712
        CorridaHorario.deleted_at.is_(None),
    )
    if sede_ids is not None:
        stmt = stmt.where(CorridaHorario.sede_id.in_(sede_ids))
    corridas = (await db.execute(stmt)).scalars().all()

    session_stmt = select(SesionClase).where(SesionClase.fecha == day)
    if sede_ids is not None:
        session_stmt = session_stmt.where(SesionClase.sede_id.in_(sede_ids))
    if tutor_id is not None:
        session_stmt = session_stmt.where(or_(SesionClase.tutor_id == tutor_id, SesionClase.tutor_cubridor_id == tutor_id))
    sessions = (await db.execute(session_stmt)).scalars().all()

    session_map = {(s.grupo_id, s.tutor_id, s.hora_inicio): s for s in sessions}
    seen: set[int] = set()
    classes: list[dict] = []
    for corrida in corridas:
        weekend = day.isoweekday()
        for assignment in (corrida.resultado_json or {}).get("asignaciones", []):
            if int(assignment.get("dia", 0)) != weekend:
                continue
            grupo_id = int(assignment["grupo_id"])
            assigned_tutor_id = int(assignment["tutor_id"])
            if tutor_id is not None and assigned_tutor_id != tutor_id:
                continue
            hora_inicio = datetime.strptime(str(assignment["hora_inicio"]), "%H:%M").time()
            session = session_map.get((grupo_id, assigned_tutor_id, hora_inicio))
            session_state = session.estado if session else "pendiente"
            if estado is not None and session_state != estado:
                continue
            if session is not None:
                seen.add(session.id)
            classes.append(
                {
                    "session": session,
                    "corrida_id": corrida.id,
                    "sede_id": corrida.sede_id,
                    "grupo_id": grupo_id,
                    "tutor_id": assigned_tutor_id,
                    "hora_inicio": assignment["hora_inicio"],
                    "hora_fin": assignment["hora_fin"],
                    "dia_semana": weekend,
                    "estado": session_state,
                    "origen": session.origen if session else "automatica",
                }
            )

    for session in sessions:
        if session.id in seen:
            continue
        if tutor_id is not None and session.tutor_id != tutor_id and session.tutor_cubridor_id != tutor_id:
            continue
        if estado is not None and session.estado != estado:
            continue
        classes.append(
            {
                "session": session,
                "corrida_id": session.corrida_id,
                "sede_id": session.sede_id,
                "grupo_id": session.grupo_id,
                "tutor_id": session.tutor_id,
                "hora_inicio": session.hora_inicio.strftime("%H:%M"),
                "hora_fin": session.hora_fin.strftime("%H:%M"),
                "dia_semana": session.dia_semana,
                "estado": session.estado,
                "origen": session.origen,
            }
        )

    group_ids = {item["grupo_id"] for item in classes}
    user_ids = {item["tutor_id"] for item in classes}
    for item in classes:
        if item["session"] is not None:
            if item["session"].tutor_cubridor_id:
                user_ids.add(item["session"].tutor_cubridor_id)
            if item["session"].registrado_por:
                user_ids.add(item["session"].registrado_por)
            if item["session"].actualizado_por:
                user_ids.add(item["session"].actualizado_por)
    sede_ids_set = {item["sede_id"] for item in classes if item["sede_id"] is not None}
    groups, materias, sedes, users = await _load_names(db, group_ids, user_ids, sede_ids_set)

    result = []
    for item in classes:
        session = item["session"]
        result.append(
            _serialize(
                session_id=session.id if session else None,
                corrida_id=item["corrida_id"],
                sede_id=item["sede_id"],
                grupo_id=item["grupo_id"],
                tutor_id=item["tutor_id"],
                fecha=day,
                dia_semana=item["dia_semana"],
                hora_inicio=item["hora_inicio"],
                hora_fin=item["hora_fin"],
                estado=item["estado"],
                tutor_cubridor_id=session.tutor_cubridor_id if session else None,
                comentario=session.comentario if session else None,
                origen=item["origen"],
                registrado_por=session.registrado_por if session else None,
                actualizado_por=session.actualizado_por if session else None,
                groups=groups,
                materias=materias,
                sedes=sedes,
                users=users,
            )
        )
    return sorted(result, key=lambda item: (item["sede_nombre"], item["hora_inicio"], item["grupo_nombre"]))


@router.post("/sesiones", status_code=201)
async def crear_sesion(
    payload: SesionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    _require_manager(user)
    if not can_manage_sede(user, payload.sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")
    _validate_estado(payload.estado)
    _validate_cubierta(payload.estado, payload.tutor_id, payload.tutor_cubridor_id)
    if payload.hora_inicio >= payload.hora_fin:
        raise HTTPException(status_code=400, detail="La hora de inicio debe ser menor a la hora de fin")
    if payload.hora_inicio.minute or payload.hora_fin.minute:
        raise HTTPException(status_code=400, detail="Las sesiones deben iniciar y terminar en horas completas")

    group = await db.get(Grupo, payload.grupo_id)
    if group is None or group.sede_id != payload.sede_id:
        raise HTTPException(status_code=400, detail="El grupo no pertenece a la sede")
    tutor = await db.get(User, payload.tutor_id)
    if tutor is None or not tutor.is_active or not tutor.es_tutor:
        raise HTTPException(status_code=400, detail="Tutor inválido")
    if payload.tutor_cubridor_id is not None:
        cubridor = await db.get(User, payload.tutor_cubridor_id)
        if cubridor is None or not cubridor.is_active or not cubridor.es_tutor:
            raise HTTPException(status_code=400, detail="Tutor cubridor inválido")
    if payload.corrida_id is not None:
        corrida = await db.get(CorridaHorario, payload.corrida_id)
        if corrida is None or corrida.sede_id != payload.sede_id:
            raise HTTPException(status_code=400, detail="Corrida inválida para la sede")

    existing = await db.execute(
        select(SesionClase).where(
            SesionClase.grupo_id == payload.grupo_id,
            SesionClase.tutor_id == payload.tutor_id,
            SesionClase.fecha == payload.fecha,
            SesionClase.hora_inicio == payload.hora_inicio,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Ya existe una sesión para ese grupo, tutor y horario")

    session = SesionClase(
        corrida_id=payload.corrida_id,
        sede_id=payload.sede_id,
        grupo_id=payload.grupo_id,
        tutor_id=payload.tutor_id,
        fecha=payload.fecha,
        dia_semana=payload.fecha.isoweekday(),
        hora_inicio=payload.hora_inicio,
        hora_fin=payload.hora_fin,
        estado=payload.estado,
        tutor_cubridor_id=payload.tutor_cubridor_id if payload.estado == "cubierta" else None,
        comentario=payload.comentario,
        origen="manual",
        registrado_por=user.id,
        actualizado_por=user.id,
    )
    db.add(session)
    await db.flush()
    groups, materias, sedes, users = await _load_names(db, {payload.grupo_id}, {payload.tutor_id, payload.tutor_cubridor_id} - {None}, {payload.sede_id})
    return _serialize(
        session_id=session.id,
        corrida_id=session.corrida_id,
        sede_id=session.sede_id,
        grupo_id=session.grupo_id,
        tutor_id=session.tutor_id,
        fecha=session.fecha,
        dia_semana=session.dia_semana,
        hora_inicio=session.hora_inicio,
        hora_fin=session.hora_fin,
        estado=session.estado,
        tutor_cubridor_id=session.tutor_cubridor_id,
        comentario=session.comentario,
        origen=session.origen,
        registrado_por=session.registrado_por,
        actualizado_por=session.actualizado_por,
        groups=groups,
        materias=materias,
        sedes=sedes,
        users=users,
    )


@router.put("/sesiones/{session_id}")
async def actualizar_sesion(
    session_id: int,
    payload: SesionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    _require_manager(user)
    session = await db.get(SesionClase, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if not can_manage_sede(user, session.sede_id):
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")

    next_state = payload.estado if payload.estado is not None else session.estado
    _validate_estado(next_state)
    if next_state == "cubierta":
        next_cubridor = payload.tutor_cubridor_id if "tutor_cubridor_id" in payload.model_fields_set else session.tutor_cubridor_id
    else:
        if "tutor_cubridor_id" in payload.model_fields_set and payload.tutor_cubridor_id is not None:
            raise HTTPException(status_code=400, detail="Solo las clases cubiertas pueden tener tutor cubridor")
        next_cubridor = None
    _validate_cubierta(next_state, session.tutor_id, next_cubridor)
    if next_cubridor is not None:
        cubridor = await db.get(User, next_cubridor)
        if cubridor is None or not cubridor.is_active or not cubridor.es_tutor:
            raise HTTPException(status_code=400, detail="Tutor cubridor inválido")

    session.estado = next_state
    session.tutor_cubridor_id = next_cubridor if next_state == "cubierta" else None
    if "comentario" in payload.model_fields_set:
        session.comentario = payload.comentario
    if session.registrado_por is None:
        session.registrado_por = user.id
    session.actualizado_por = user.id
    await db.flush()

    user_ids = {session.tutor_id, session.actualizado_por} - {None}
    if session.tutor_cubridor_id:
        user_ids.add(session.tutor_cubridor_id)
    groups, materias, sedes, users = await _load_names(db, {session.grupo_id}, user_ids, {session.sede_id})
    return _serialize(
        session_id=session.id,
        corrida_id=session.corrida_id,
        sede_id=session.sede_id,
        grupo_id=session.grupo_id,
        tutor_id=session.tutor_id,
        fecha=session.fecha,
        dia_semana=session.dia_semana,
        hora_inicio=session.hora_inicio,
        hora_fin=session.hora_fin,
        estado=session.estado,
        tutor_cubridor_id=session.tutor_cubridor_id,
        comentario=session.comentario,
        origen=session.origen,
        registrado_por=session.registrado_por,
        actualizado_por=session.actualizado_por,
        groups=groups,
        materias=materias,
        sedes=sedes,
        users=users,
    )


@router.get("/mia")
async def mis_sesiones(
    desde: date | None = None,
    hasta: date | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    stmt = select(SesionClase).where(or_(SesionClase.tutor_id == user.id, SesionClase.tutor_cubridor_id == user.id))
    if desde is not None:
        stmt = stmt.where(SesionClase.fecha >= desde)
    if hasta is not None:
        stmt = stmt.where(SesionClase.fecha <= hasta)
    sessions = (await db.execute(stmt.order_by(SesionClase.fecha.desc(), SesionClase.hora_inicio.desc()))).scalars().all()

    group_ids = {s.grupo_id for s in sessions}
    user_ids = {s.tutor_id for s in sessions}
    for s in sessions:
        if s.tutor_cubridor_id:
            user_ids.add(s.tutor_cubridor_id)
        if s.actualizado_por:
            user_ids.add(s.actualizado_por)
    sede_ids = {s.sede_id for s in sessions}
    groups, materias, sedes, users = await _load_names(db, group_ids, user_ids, sede_ids)

    counts = defaultdict(int)
    result = []
    for session in sessions:
        item = _serialize(
            session_id=session.id,
            corrida_id=session.corrida_id,
            sede_id=session.sede_id,
            grupo_id=session.grupo_id,
            tutor_id=session.tutor_id,
            fecha=session.fecha,
            dia_semana=session.dia_semana,
            hora_inicio=session.hora_inicio,
            hora_fin=session.hora_fin,
            estado=session.estado,
            tutor_cubridor_id=session.tutor_cubridor_id,
            comentario=session.comentario,
            origen=session.origen,
            registrado_por=session.registrado_por,
            actualizado_por=session.actualizado_por,
            groups=groups,
            materias=materias,
            sedes=sedes,
            users=users,
            current_user=user,
        )
        counts[session.estado] += 1
        if item["impartida_por_mi"]:
            counts["impartidas"] += 1
        result.append(item)

    return {
        "resumen": {
            "total": len(result),
            "impartidas": counts["impartidas"],
            "asistio": counts["asistio"],
            "retardo": counts["retardo"],
            "falta": counts["falta"],
            "justificada": counts["justificada"],
            "cancelada": counts["cancelada"],
            "cubierta": counts["cubierta"],
            "pendiente": counts["pendiente"],
        },
        "sesiones": result,
    }
