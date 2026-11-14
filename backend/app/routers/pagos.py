from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.pago import Cargo, Pago
from app.models.sede import Sede
from app.models.student import Student
from app.models.user import User
from app.services.pdf import build_recibo_pdf
from app.schemas.inscripcion import CargoRead, PagoRead
from app.schemas.pago import (
    ComprobanteRead,
    PagoAdminRead,
    PagoCreate,
    PagoPage,
    PagoValidar,
    SimulacroOptInResponse,
)
from app.services.inscripcion import get_config
from app.services.notificaciones import enqueue_notificacion, student_context
from app.services.pagos import (
    PagoError,
    adjuntar_comprobante,
    opt_in_simulacro,
    registrar_pago,
    validar_pago,
)
from app.services.storage import presigned_payment_proof_url, upload_payment_proof

router = APIRouter(prefix="/pagos", tags=["pagos"])

STAFF_ROLES = ("admin", "coordinador", "subcoordinador", "inscripcion")
CASH_ROLES = ("admin", "coordinador", "subcoordinador", "inscripcion")
VALIDATION_ROLES = ("admin", "coordinador", "subcoordinador")


def _require_staff(user: User) -> None:
    if user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Rol no autorizado")


def _require_sede(user: User, sede_id: int | None) -> None:
    if user.role == "admin":
        return
    if sede_id is None or user.sede_id != sede_id:
        raise HTTPException(status_code=403, detail="No autorizado para esta sede")


async def _student_for_user(db: AsyncSession, user: User) -> Student:
    result = await db.execute(
        select(Student).where(Student.user_id == user.id, Student.deleted_at.is_(None))
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise HTTPException(status_code=404, detail="No tienes una inscripción registrada")
    return student


async def _pago_admin_payload(db: AsyncSession, pago: Pago) -> dict:
    student = await db.get(Student, pago.student_id)
    cargo = await db.get(Cargo, pago.cargo_id)
    data = PagoRead.model_validate(pago).model_dump()
    data.update(
        student_id=pago.student_id,
        matricula=student.matricula if student else None,
        student_name=student.full_name if student else None,
        cargo_concepto=cargo.concepto if cargo else None,
        comprobante_url=presigned_payment_proof_url(pago.comprobante_key)
        if pago.comprobante_key
        else None,
    )
    return data


@router.post("/simulacro", response_model=SimulacroOptInResponse)
async def solicitar_simulacro(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.role != "alumno":
        raise HTTPException(status_code=403, detail="Sólo alumnos pueden solicitar el simulacro")
    student = await _student_for_user(db, user)
    config = await get_config(db)
    if not config.simulacro_activo:
        raise HTTPException(status_code=409, detail="El simulacro no está disponible")
    cargo, created = await opt_in_simulacro(db, student, config)
    if cargo is not None and student.email:
        sede = await db.get(Sede, student.sede_id) if student.sede_id else None
        context = student_context(student, sede, config)
        context["monto"] = str(cargo.monto)
        context["moneda"] = cargo.moneda
        await enqueue_notificacion(
            db,
            "simulacro_confirmado",
            student,
            student.email,
            context=context,
            dedupe_key=f"simulacro_confirmado:{student.id}",
        )
    return SimulacroOptInResponse(
        cargo=CargoRead.model_validate(cargo) if cargo else None,
        creado=created,
    )


@router.get("/me", response_model=list[PagoRead])
async def my_pagos(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    student = await _student_for_user(db, user)
    result = await db.execute(
        select(Pago)
        .where(Pago.student_id == student.id, Pago.deleted_at.is_(None))
        .order_by(Pago.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=PagoRead, status_code=201)
async def create_pago(
    payload: PagoCreate,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    cargo = await db.get(Cargo, payload.cargo_id)
    if cargo is None or cargo.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Cargo no encontrado")
    student = await db.get(Student, cargo.student_id)
    if student is None or student.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")

    if user.role == "alumno":
        own = await _student_for_user(db, user)
        if own.id != student.id:
            raise HTTPException(status_code=403, detail="No autorizado para este cargo")
        if payload.metodo != "transferencia":
            raise HTTPException(status_code=403, detail="Sólo puedes registrar transferencias")
    else:
        _require_staff(user)
        _require_sede(user, student.sede_id)
        if payload.metodo == "efectivo" and user.role not in CASH_ROLES:
            raise HTTPException(status_code=403, detail="Rol no autorizado para efectivo")

    config = await get_config(db)
    try:
        pago = await registrar_pago(
            db,
            student,
            cargo,
            monto=payload.monto,
            metodo=payload.metodo,
            config=config,
            actor_id=user.id,
            referencia=payload.referencia,
            fecha_pago=payload.fecha_pago,
        )
    except PagoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return pago


@router.post("/{pago_id}/comprobante", response_model=ComprobanteRead)
async def upload_comprobante(
    pago_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    pago = await db.get(Pago, pago_id)
    if pago is None or pago.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    student = await db.get(Student, pago.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    if user.role == "alumno":
        own = await _student_for_user(db, user)
        if own.id != pago.student_id:
            raise HTTPException(status_code=403, detail="No autorizado para este pago")
    else:
        _require_staff(user)
        _require_sede(user, student.sede_id)

    proof = await upload_payment_proof(file, pago.student_id, pago.id)
    try:
        await adjuntar_comprobante(db, pago, proof, actor_id=user.id)
    except PagoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    if student.email:
        sede = await db.get(Sede, student.sede_id) if student.sede_id else None
        context = student_context(student, sede)
        context["monto"] = str(pago.monto)
        context["moneda"] = pago.moneda
        await enqueue_notificacion(
            db,
            "pago_recibido",
            student,
            student.email,
            context=context,
            dedupe_key=f"pago_recibido:{pago.id}",
        )
    return ComprobanteRead(
        pago_id=pago.id,
        nombre=pago.comprobante_nombre or "",
        content_type=pago.comprobante_content_type or "",
        size=pago.comprobante_size or 0,
    )


@router.post("/{pago_id}/validar", response_model=PagoAdminRead)
async def validate_pago(
    pago_id: int,
    payload: PagoValidar,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    if user.role not in VALIDATION_ROLES:
        raise HTTPException(status_code=403, detail="Rol no autorizado para validar pagos")
    pago = await db.get(Pago, pago_id)
    if pago is None or pago.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    student = await db.get(Student, pago.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    _require_sede(user, student.sede_id)
    try:
        pago = await validar_pago(db, pago, payload.aprobado, user.id, payload.motivo)
    except PagoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    await db.refresh(pago)
    if student.email:
        sede = await db.get(Sede, student.sede_id) if student.sede_id else None
        context = student_context(student, sede)
        context["monto"] = str(pago.monto)
        context["moneda"] = pago.moneda
        context["recibo"] = pago.recibo_codigo or ""
        context["motivo"] = pago.motivo_rechazo or ""
        clave = "pago_validado" if payload.aprobado else "pago_rechazado"
        await enqueue_notificacion(
            db,
            clave,
            student,
            student.email,
            context=context,
            dedupe_key=f"{clave}:{pago.id}",
        )
    return await _pago_admin_payload(db, pago)


@router.get("/{pago_id}/comprobante")
async def get_comprobante_url(
    pago_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    pago = await db.get(Pago, pago_id)
    if pago is None or pago.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    student = await db.get(Student, pago.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    if user.role == "alumno":
        own = await _student_for_user(db, user)
        if own.id != pago.student_id:
            raise HTTPException(status_code=403, detail="No autorizado para este pago")
    else:
        _require_staff(user)
        _require_sede(user, student.sede_id)
    if not pago.comprobante_key:
        raise HTTPException(status_code=404, detail="El pago no tiene comprobante")
    url = presigned_payment_proof_url(pago.comprobante_key)
    if url is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Almacenamiento privado no configurado en el servidor "
                "(falta R2_PRIVATE_BUCKET)."
            ),
        )
    return {"url": url, "expires_in": 900}


@router.get("/{pago_id}/recibo")
async def download_recibo(
    pago_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    pago = await db.get(Pago, pago_id)
    if pago is None or pago.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    student = await db.get(Student, pago.student_id)
    cargo = await db.get(Cargo, pago.cargo_id)
    if student is None or cargo is None:
        raise HTTPException(status_code=404, detail="Datos del pago incompletos")
    if user.role == "alumno":
        own = await _student_for_user(db, user)
        if own.id != pago.student_id:
            raise HTTPException(status_code=403, detail="No autorizado para este pago")
    else:
        _require_staff(user)
        _require_sede(user, student.sede_id)
    if pago.estado != "validado" or not pago.recibo_codigo:
        raise HTTPException(status_code=409, detail="El pago aún no tiene recibo válido")
    sede = await db.get(Sede, student.sede_id) if student.sede_id else None
    content = build_recibo_pdf(pago, cargo, student, sede)
    filename = f"recibo-{pago.recibo_codigo}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{pago_id}", response_model=PagoAdminRead)
async def get_pago(
    pago_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    pago = await db.get(Pago, pago_id)
    if pago is None or pago.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    student = await db.get(Student, pago.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    if user.role == "alumno":
        own = await _student_for_user(db, user)
        if own.id != pago.student_id:
            raise HTTPException(status_code=403, detail="No autorizado para este pago")
    else:
        _require_staff(user)
        _require_sede(user, student.sede_id)
    return await _pago_admin_payload(db, pago)


@router.get("", response_model=PagoPage)
async def list_pagos(
    estatus: str | None = None,
    metodo: str | None = None,
    sede_id: int | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    _require_staff(user)
    stmt = select(Pago).join(Student, Student.id == Pago.student_id).where(
        Pago.deleted_at.is_(None)
    )
    if user.role != "admin":
        if user.sede_id is None:
            raise HTTPException(status_code=403, detail="Usuario sin sede asignada")
        stmt = stmt.where(Student.sede_id == user.sede_id)
    elif sede_id is not None:
        stmt = stmt.where(Student.sede_id == sede_id)
    if estatus:
        stmt = stmt.where(Pago.estado == estatus)
    if metodo:
        stmt = stmt.where(Pago.metodo == metodo)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Student.full_name.ilike(term),
                Student.matricula.ilike(term),
                Pago.referencia.ilike(term),
                Pago.recibo_codigo.ilike(term),
            )
        )
    total = await db.execute(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(
        stmt.order_by(Pago.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [await _pago_admin_payload(db, pago) for pago in result.scalars().all()]
    return PagoPage(
        items=items,
        total=int(total.scalar_one()),
        page=page,
        page_size=page_size,
    )
