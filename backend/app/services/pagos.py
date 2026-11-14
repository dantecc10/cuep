from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inscripcion import ConfiguracionInscripcion, EventoInscripcion
from app.models.pago import Cargo, Pago
from app.models.student import Student


async def crear_cargo_simulacro(
    db: AsyncSession,
    student: Student,
    config: ConfiguracionInscripcion,
    created_by: int | None = None,
) -> Cargo | None:
    if not config.simulacro_activo or Decimal(config.simulacro_monto) <= 0:
        return None
    existing = await db.execute(
        select(Cargo).where(
            Cargo.student_id == student.id,
            Cargo.anio == config.anio,
            Cargo.concepto == "simulacro",
            Cargo.deleted_at.is_(None),
        )
    )
    cargo = existing.scalar_one_or_none()
    if cargo is not None:
        return cargo
    cargo = Cargo(
        student_id=student.id,
        anio=config.anio,
        concepto="simulacro",
        descripcion="Pago de simulacro de admisión",
        monto=config.simulacro_monto,
        moneda=config.simulacro_moneda,
        estado="pendiente",
        created_by=created_by,
    )
    db.add(cargo)
    await db.flush()
    return cargo


async def calcular_saldo(db: AsyncSession, student_id: int) -> Decimal:
    cargos = await db.execute(
        select(Cargo.monto, Cargo.estado).where(
            Cargo.student_id == student_id,
            Cargo.deleted_at.is_(None),
            Cargo.estado.notin_(("cancelado", "exento")),
        )
    )
    total = sum((Decimal(row.monto) for row in cargos), Decimal("0"))

    pagos = await db.execute(
        select(func.coalesce(func.sum(Pago.monto), 0)).where(
            Pago.student_id == student_id,
            Pago.estado == "validado",
            Pago.deleted_at.is_(None),
        )
    )
    pagado = Decimal(pagos.scalar_one() or 0)
    return max(total - pagado, Decimal("0"))


class PagoError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def saldo_cargo(db: AsyncSession, cargo: Cargo) -> Decimal:
    pagado_result = await db.execute(
        select(func.coalesce(func.sum(Pago.monto), 0)).where(
            Pago.cargo_id == cargo.id,
            Pago.estado == "validado",
            Pago.deleted_at.is_(None),
        )
    )
    pagado = Decimal(pagado_result.scalar_one() or 0)
    return max(Decimal(cargo.monto) - pagado, Decimal("0"))


async def sync_cargo_estado(db: AsyncSession, cargo: Cargo) -> None:
    if cargo.estado in ("cancelado", "exento"):
        return
    pagado_result = await db.execute(
        select(func.coalesce(func.sum(Pago.monto), 0)).where(
            Pago.cargo_id == cargo.id,
            Pago.estado == "validado",
            Pago.deleted_at.is_(None),
        )
    )
    pagado = Decimal(pagado_result.scalar_one() or 0)
    if pagado >= Decimal(cargo.monto):
        cargo.estado = "pagado"
    elif pagado > 0:
        cargo.estado = "parcial"
    else:
        cargo.estado = "pendiente"
    await db.flush()


async def get_cargo_simulacro(
    db: AsyncSession, student_id: int, anio: int
) -> Cargo | None:
    result = await db.execute(
        select(Cargo).where(
            Cargo.student_id == student_id,
            Cargo.anio == anio,
            Cargo.concepto == "simulacro",
            Cargo.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def opt_in_simulacro(
    db: AsyncSession, student: Student, config: ConfiguracionInscripcion
) -> tuple[Cargo | None, bool]:
    existing = await get_cargo_simulacro(db, student.id, config.anio)
    if existing is not None:
        return existing, False
    cargo = await crear_cargo_simulacro(db, student, config)
    return cargo, cargo is not None


async def registrar_pago(
    db: AsyncSession,
    student: Student,
    cargo: Cargo,
    monto: Decimal,
    metodo: str,
    config: ConfiguracionInscripcion,
    actor_id: int | None = None,
    referencia: str | None = None,
    fecha_pago: datetime | None = None,
) -> Pago:
    if cargo.student_id != student.id:
        raise PagoError("El cargo no pertenece al alumno.", 404)
    if cargo.deleted_at is not None or cargo.estado in ("cancelado", "exento"):
        raise PagoError("El cargo no está disponible para pago.", 409)
    if metodo == "efectivo":
        if not config.pago_efectivo_habilitado:
            raise PagoError("El pago en efectivo está deshabilitado.", 403)
        if actor_id is None:
            raise PagoError("Sólo el personal puede registrar pagos en efectivo.", 403)
    elif metodo == "transferencia":
        if not config.transferencia_habilitada:
            raise PagoError("La transferencia está deshabilitada.", 403)
    else:
        raise PagoError("Método de pago inválido.", 422)

    monto = Decimal(str(monto))
    pendiente = await saldo_cargo(db, cargo)
    if monto <= 0:
        raise PagoError("El monto debe ser mayor a cero.", 422)
    if monto > pendiente:
        raise PagoError(
            f"El monto excede el saldo pendiente del cargo ({pendiente:.2f}).", 422
        )

    now = datetime.now(timezone.utc)
    pago = Pago(
        cargo_id=cargo.id,
        student_id=student.id,
        monto=monto,
        moneda=cargo.moneda,
        metodo=metodo,
        estado="validado" if metodo == "efectivo" else "pendiente",
        referencia=referencia,
        fecha_pago=fecha_pago or now,
        validado_por=actor_id if metodo == "efectivo" else None,
        validado_at=now if metodo == "efectivo" else None,
    )
    db.add(pago)
    await db.flush()
    if metodo == "efectivo":
        pago.recibo_codigo = f"REC-{now.year}-{pago.id:06d}"
        pago.recibo_emitido_at = now
        db.add(
            EventoInscripcion(
                student_id=student.id,
                tipo="pago_efectivo",
                estado_anterior=cargo.estado,
                estado_nuevo=cargo.estado,
                actor_id=actor_id,
                sede_id=student.sede_id,
                detalle={
                    "pago_id": pago.id,
                    "cargo_id": cargo.id,
                    "monto": str(monto),
                    "metodo": metodo,
                },
            )
        )
    await sync_cargo_estado(db, cargo)
    await db.flush()
    return pago


async def adjuntar_comprobante(
    db: AsyncSession,
    pago: Pago,
    proof: dict[str, str | int],
    actor_id: int | None = None,
) -> Pago:
    if pago.estado != "pendiente":
        raise PagoError("El pago ya no está pendiente de comprobante.", 409)
    if pago.metodo != "transferencia":
        raise PagoError("El comprobante sólo aplica a transferencias.", 422)
    pago.comprobante_key = str(proof["key"])
    pago.comprobante_nombre = str(proof["nombre"])
    pago.comprobante_content_type = str(proof["content_type"])
    pago.comprobante_size = int(proof["size"])
    pago.comprobante_subido_at = datetime.now(timezone.utc)
    db.add(
        EventoInscripcion(
            student_id=pago.student_id,
            tipo="pago_comprobante",
            actor_id=actor_id,
            detalle={
                "pago_id": pago.id,
                "cargo_id": pago.cargo_id,
                "monto": str(pago.monto),
            },
        )
    )
    await db.flush()
    return pago


async def validar_pago(
    db: AsyncSession,
    pago: Pago,
    aprobado: bool,
    actor_id: int,
    motivo: str | None = None,
) -> Pago:
    if pago.estado != "pendiente":
        raise PagoError("El pago ya fue procesado.", 409)
    now = datetime.now(timezone.utc)
    cargo = await db.get(Cargo, pago.cargo_id)
    if cargo is None:
        raise PagoError("Cargo no encontrado.", 404)
    if aprobado and not pago.comprobante_key:
        raise PagoError("No puedes validar un pago sin comprobante.", 409)
    anterior = pago.estado
    if aprobado:
        pago.estado = "validado"
        pago.validado_por = actor_id
        pago.validado_at = now
        if not pago.recibo_codigo:
            pago.recibo_codigo = f"REC-{now.year}-{pago.id:06d}"
            pago.recibo_emitido_at = now
        tipo = "pago_validado"
    else:
        pago.estado = "rechazado"
        pago.motivo_rechazo = motivo
        tipo = "pago_rechazado"
    db.add(
        EventoInscripcion(
            student_id=pago.student_id,
            tipo=tipo,
            estado_anterior=anterior,
            estado_nuevo=pago.estado,
            actor_id=actor_id,
            detalle={"pago_id": pago.id, "motivo": motivo} if motivo else {"pago_id": pago.id},
        )
    )
    await sync_cargo_estado(db, cargo)
    await db.flush()
    return pago
