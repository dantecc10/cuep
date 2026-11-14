import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_user, require_role
from app.models.inscripcion import EventoInscripcion
from app.models.pago import Cargo, Pago
from app.models.sede import Sede
from app.models.student import Student
from app.models.user import User
from app.services.pdf import build_pase_pdf
from app.schemas.inscripcion import (
    CheckInRequest,
    CheckInResponse,
    ConfiguracionInscripcionPublica,
    ConfiguracionInscripcionUpdate,
    EstadoUpdate,
    EventoInscripcionRead,
    InscripcionMe,
    InscripcionPage,
    InscripcionRead,
)
from app.services.inscripcion import (
    InscripcionError,
    find_student_by_identifier,
    get_config,
    get_inscripcion_me,
    pase_url,
)
from app.services.notificaciones import enqueue_notificacion, student_context
from app.services.pagos import calcular_saldo

router = APIRouter(prefix="/inscripciones", tags=["inscripciones"])

STAFF_ROLES = ("admin", "coordinador", "subcoordinador", "inscripcion")


def _require_staff(user: User) -> None:
    if user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Rol no autorizado")


def _require_sede_access(user: User, sede_id: int | None) -> None:
    if user.role == "admin":
        return
    if sede_id is None or user.sede_id != sede_id:
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")


def _student_payload(student: Student) -> dict:
    data = InscripcionRead.model_validate(student).model_dump()
    data["pase_url"] = pase_url(student.qr_token)
    return data


@router.get("/config", response_model=ConfiguracionInscripcionPublica)
async def get_public_config(db: AsyncSession = Depends(get_async_db)):
    return await get_config(db)


@router.put("/config", response_model=ConfiguracionInscripcionPublica)
async def update_config(
    payload: ConfiguracionInscripcionUpdate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(require_role("admin")),
):
    config = await get_config(db, for_update=True)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    config.updated_by = user.id
    await db.flush()
    await db.refresh(config)
    return config


@router.get("/me", response_model=InscripcionMe)
async def get_my_inscripcion(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    try:
        data = await get_inscripcion_me(db, user)
    except InscripcionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    payload = _student_payload(data["student"])
    payload.update(
        cargos=data["cargos"],
        pagos=data["pagos"],
        eventos=data["eventos"],
        saldo=data["saldo"],
        pase_url=data["pase_url"],
    )
    return payload


@router.get("/me/pase")
async def download_my_pase(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    try:
        data = await get_inscripcion_me(db, user)
    except InscripcionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    student = data["student"]
    config = await get_config(db)
    sede = await db.get(Sede, student.sede_id) if student.sede_id else None
    content = build_pase_pdf(student, sede, config)
    filename = f"pase-{student.matricula or student.id}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{student_id}/pase")
async def download_pase(
    student_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    _require_staff(user)
    student = await _get_student_or_404(db, student_id)
    _require_sede_access(user, student.sede_id)
    config = await get_config(db)
    sede = await db.get(Sede, student.sede_id) if student.sede_id else None
    content = build_pase_pdf(student, sede, config)
    filename = f"pase-{student.matricula or student.id}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/checkin", response_model=CheckInResponse)
async def checkin(
    payload: CheckInRequest,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    _require_staff(user)
    student = await find_student_by_identifier(db, payload.identificador)
    if student is None:
        raise HTTPException(status_code=404, detail="No se encontró la inscripción")
    target_sede = payload.sede_id or student.sede_id
    _require_sede_access(user, student.sede_id)
    if payload.sede_id is not None:
        _require_sede_access(user, payload.sede_id)
    if student.estatus in ("cancelado", "baja"):
        raise HTTPException(status_code=409, detail="La inscripción está cancelada o de baja")

    already = student.checkin_at is not None
    if not already:
        student.checkin_at = datetime.now(timezone.utc)
        student.checkin_by = user.id
        student.checkin_sede_id = target_sede
        db.add(
            EventoInscripcion(
                student_id=student.id,
                tipo="checkin",
                estado_anterior=student.estatus,
                estado_nuevo=student.estatus,
                actor_id=user.id,
                sede_id=target_sede,
                detalle={"metodo": "staff"},
            )
        )
        await db.flush()
        if student.email:
            sede = await db.get(Sede, target_sede) if target_sede else None
            await enqueue_notificacion(
                db,
                "checkin_confirmado",
                student,
                student.email,
                context=student_context(student, sede),
                dedupe_key=f"checkin_confirmado:{student.id}",
            )
    return CheckInResponse(
        student_id=student.id,
        matricula=student.matricula,
        nombre=student.full_name,
        estatus=student.estatus,
        checkin_at=student.checkin_at,
        ya_registrado=already,
    )


@router.get("/export.csv")
async def export_inscripciones(
    anio: int | None = None,
    sede_id: int | None = None,
    estatus: str | None = None,
    nivel: str | None = None,
    area: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("admin", "coordinador", "subcoordinador"):
        raise HTTPException(status_code=403, detail="Rol no autorizado para exportar")
    stmt = select(Student).where(Student.deleted_at.is_(None))
    if user.role != "admin":
        if user.sede_id is None:
            raise HTTPException(status_code=403, detail="Usuario sin sede asignada")
        stmt = stmt.where(Student.sede_id == user.sede_id)
    elif sede_id is not None:
        stmt = stmt.where(Student.sede_id == sede_id)
    if anio is not None:
        stmt = stmt.where(Student.anio == anio)
    if estatus:
        stmt = stmt.where(Student.estatus == estatus)
    if nivel:
        stmt = stmt.where(Student.nivel == nivel)
    if area:
        stmt = stmt.where(Student.area == area)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Student.full_name.ilike(term),
                Student.matricula.ilike(term),
                Student.email.ilike(term),
                Student.phone.ilike(term),
            )
        )
    result = await db.execute(stmt.order_by(Student.created_at.asc()))
    students = result.scalars().all()
    sede_ids = {student.sede_id for student in students if student.sede_id}
    sedes = {}
    if sede_ids:
        sedes_result = await db.execute(select(Sede).where(Sede.id.in_(sede_ids)))
        sedes = {sede.id: sede for sede in sedes_result.scalars().all()}

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "matricula",
            "folio",
            "nombre",
            "email",
            "telefono",
            "nivel",
            "area",
            "sede",
            "estatus",
            "anio",
            "checkin_at",
            "created_at",
        ]
    )
    for student in students:
        writer.writerow(
            [
                student.matricula or "",
                student.folio or "",
                student.full_name or "",
                student.email or "",
                student.phone or "",
                student.nivel,
                student.area or "",
                sedes[student.sede_id].nombre if student.sede_id in sedes else "",
                student.estatus,
                student.anio,
                student.checkin_at.isoformat() if student.checkin_at else "",
                student.created_at.isoformat() if student.created_at else "",
            ]
        )
    filename = f"inscripciones-{anio or 'todas'}.csv"
    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("", response_model=InscripcionPage)
async def list_inscripciones(
    anio: int | None = None,
    sede_id: int | None = None,
    estatus: str | None = None,
    nivel: str | None = None,
    area: str | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    _require_staff(user)
    stmt = select(Student).where(Student.deleted_at.is_(None))
    if user.role != "admin":
        if user.sede_id is None:
            raise HTTPException(status_code=403, detail="Usuario sin sede asignada")
        stmt = stmt.where(Student.sede_id == user.sede_id)
    elif sede_id is not None:
        stmt = stmt.where(Student.sede_id == sede_id)
    if anio is not None:
        stmt = stmt.where(Student.anio == anio)
    if estatus:
        stmt = stmt.where(Student.estatus == estatus)
    if nivel:
        stmt = stmt.where(Student.nivel == nivel)
    if area:
        stmt = stmt.where(Student.area == area)
    if search:
        term = f"%{search.strip()}%"
        digits = "".join(char for char in search if char.isdigit())
        conditions = [
            Student.full_name.ilike(term),
            Student.matricula.ilike(term),
            Student.email.ilike(term),
            Student.phone.ilike(term),
        ]
        if len(digits) >= 10:
            conditions.append(Student.phone_normalized == digits[-10:])
        stmt = stmt.where(or_(*conditions))

    total = await db.execute(select(func.count()).select_from(stmt.subquery()))
    sort_fields = {
        "created_at": Student.created_at,
        "full_name": Student.full_name,
        "matricula": Student.matricula,
        "estatus": Student.estatus,
        "checkin_at": Student.checkin_at,
    }
    sort_column = sort_fields.get(sort_by, Student.created_at)
    stmt = stmt.order_by(
        sort_column.desc() if sort_dir.lower() == "desc" else sort_column.asc()
    ).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return InscripcionPage(
        items=[_student_payload(student) for student in result.scalars().all()],
        total=int(total.scalar_one()),
        page=page,
        page_size=page_size,
    )


async def _get_student_or_404(db: AsyncSession, student_id: int) -> Student:
    student = await db.get(Student, student_id)
    if student is None or student.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    return student


@router.get("/{student_id}", response_model=InscripcionMe)
async def get_inscripcion(
    student_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    _require_staff(user)
    student = await _get_student_or_404(db, student_id)
    _require_sede_access(user, student.sede_id)
    cargos_result = await db.execute(
        select(Cargo)
        .where(Cargo.student_id == student.id, Cargo.deleted_at.is_(None))
        .order_by(Cargo.created_at.desc())
    )
    pagos_result = await db.execute(
        select(Pago)
        .where(Pago.student_id == student.id, Pago.deleted_at.is_(None))
        .order_by(Pago.created_at.desc())
    )
    eventos_result = await db.execute(
        select(EventoInscripcion)
        .where(EventoInscripcion.student_id == student.id)
        .order_by(EventoInscripcion.created_at.desc())
        .limit(50)
    )
    payload = _student_payload(student)
    payload.update(
        cargos=cargos_result.scalars().all(),
        pagos=pagos_result.scalars().all(),
        eventos=eventos_result.scalars().all(),
        saldo=float(await calcular_saldo(db, student.id)),
    )
    return payload


@router.get("/{student_id}/eventos", response_model=list[EventoInscripcionRead])
async def list_eventos(
    student_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    _require_staff(user)
    student = await _get_student_or_404(db, student_id)
    _require_sede_access(user, student.sede_id)
    result = await db.execute(
        select(EventoInscripcion)
        .where(EventoInscripcion.student_id == student.id)
        .order_by(EventoInscripcion.created_at.desc())
    )
    return result.scalars().all()


@router.patch("/{student_id}/estatus", response_model=InscripcionRead)
async def update_estatus(
    student_id: int,
    payload: EstadoUpdate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.role not in ("admin", "coordinador", "subcoordinador"):
        raise HTTPException(status_code=403, detail="Rol no autorizado para cambiar estatus")
    student = await _get_student_or_404(db, student_id)
    _require_sede_access(user, student.sede_id)
    previous = student.estatus
    if previous == payload.estatus:
        return _student_payload(student)
    student.estatus = payload.estatus
    db.add(
        EventoInscripcion(
            student_id=student.id,
            tipo="cambio_estatus",
            estado_anterior=previous,
            estado_nuevo=payload.estatus,
            actor_id=user.id,
            sede_id=student.sede_id,
            detalle={"motivo": payload.motivo} if payload.motivo else None,
        )
    )
    await db.flush()
    await db.refresh(student)
    return _student_payload(student)
