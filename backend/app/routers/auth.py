from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_async_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token, get_password_hash
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.student import Student
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.models.sede import Sede
from app.schemas.inscripcion import InscripcionCreate, RegistroResponse
from app.services.inscripcion import InscripcionError, pase_url, register_inscripcion
from app.services.notificaciones import enqueue_notificacion, student_context
from app.core.cookies import clear_refresh_cookie, set_refresh_cookie
from app.schemas.user import UserRead, UserProfileUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(User).where(func.lower(User.email) == payload.email.strip().lower())
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    if user.totp_enabled:
        import secrets
        import hashlib
        from datetime import datetime, timedelta, timezone
        code = f"{secrets.randbelow(1000000):06d}"
        challenge_id = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        from app.models.two_factor import TwoFactorChallenge
        ch = TwoFactorChallenge(
            user_id=user.id,
            challenge_id=challenge_id,
            otp_hash=hashlib.sha256(code.encode()).hexdigest(),
            expires_at=expires_at,
        )
        db.add(ch)
        await db.flush()
        from app.services.email import send_email_sync
        from fastapi.concurrency import run_in_threadpool
        await run_in_threadpool(send_email_sync, user.email, "Código de verificación CUEP", f"Tu código de verificación es: {code}\nExpira en 10 minutos.")
        return {"requires_2fa": True, "challenge_id": challenge_id, "methods": ["email", "totp"]}

    access = create_access_token(str(user.id))
    set_refresh_cookie(response, create_refresh_token(str(user.id)))
    return TokenResponse(access_token=access)



@router.post("/register", status_code=201, response_model=RegistroResponse)
async def register(payload: InscripcionCreate, db: AsyncSession = Depends(get_async_db)):
    try:
        user, student, config = await register_inscripcion(db, payload)
    except InscripcionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    sede = await db.get(Sede, student.sede_id) if student.sede_id else None
    context = student_context(student, sede, config)
    await enqueue_notificacion(
        db,
        "registro_confirmado",
        student,
        user.email,
        context=context,
        dedupe_key=f"registro_confirmado:{student.id}",
    )
    if payload.solicita_simulacro:
        await enqueue_notificacion(
            db,
            "simulacro_confirmado",
            student,
            user.email,
            context=context,
            dedupe_key=f"simulacro_confirmado:{student.id}",
        )
    return RegistroResponse(
        id=user.id,
        student_id=student.id,
        email=user.email,
        role=user.role,
        matricula=student.matricula or "",
        qr_token=student.qr_token or "",
        estatus=student.estatus,
        anio=config.anio,
        pase_url=pase_url(student.qr_token) or "",
    )


@router.post("/register-tutor", status_code=201)
async def register_tutor(payload: dict, db: AsyncSession = Depends(get_async_db)):
    # Reuse basic user fields; tutor profile is optional
    email = payload.get("email")
    password = payload.get("password")
    nombre = payload.get("nombre")
    apellido_paterno = payload.get("apellido_paterno")
    apellido_materno = payload.get("apellido_materno")
    telefono = payload.get("telefono")
    if not email or not password or not nombre or not apellido_paterno:
        raise HTTPException(status_code=422, detail="Datos incompletos")
    exists = await db.execute(select(User).where(User.email == email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        nombre=nombre,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        role="tutor",
        es_tutor=False,
        telefono=telefono,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return {"id": user.id, "email": user.email, "role": user.role, "estado": "pendiente_aprobacion"}

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = Body(default=None),
    db: AsyncSession = Depends(get_async_db),
):
    from app.core.config import settings

    token = request.cookies.get(settings.REFRESH_COOKIE_NAME) or (payload.refresh_token if payload else None)
    decoded = decode_token(token) if token else None
    if decoded is None or decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh inválido")
    try:
        user_id = int(decoded["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh inválido") from None
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    set_refresh_cookie(response, create_refresh_token(str(user.id)))
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/logout", status_code=204)
async def logout(response: Response):
    clear_refresh_cookie(response)
    return None


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me/profile", response_model=UserRead)
async def update_my_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    for field in (
        "nombre",
        "apellido_paterno",
        "apellido_materno",
        "telefono",
        "biografia_md",
        "foto_url",
        "carga_max_horas",
        "area_principal",
    ):
        value = getattr(payload, field, None)
        if value is not None:
            setattr(user, field, value)
    if payload.foto_url is not None and user.role == "alumno":
        student_result = await db.execute(select(Student).where(Student.user_id == user.id))
        student = student_result.scalar_one_or_none()
        if student is not None:
            student.photo_url = payload.foto_url
    await db.flush()
    await db.refresh(user)
    return user
