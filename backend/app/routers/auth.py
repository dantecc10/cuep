from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_async_db
from app.core.security import verify_password, create_access_token, decode_token, get_password_hash
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.student import Student
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
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
    return TokenResponse(access_token=access)



@router.post("/register", status_code=201)
async def register(payload: dict, db: AsyncSession = Depends(get_async_db)):
    from app.schemas.student import StudentRegister
    data = StudentRegister(**payload)
    # validate sede
    from app.models.sede import Sede
    sede = await db.get(Sede, data.sede_id)
    if sede is None:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    # check duplicate email
    exists = await db.execute(select(User).where(User.email == data.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email ya registrado")
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        nombre=data.nombre,
        apellido_paterno=data.apellido_paterno,
        apellido_materno=data.apellido_materno,
        role="alumno",
        es_tutor=False,
        telefono=data.telefono,
    )
    db.add(user)
    await db.flush()
    student = Student(user_id=user.id, sede_id=data.sede_id, nivel=data.nivel, area=data.area, estatus="activo")
    db.add(student)
    await db.flush()
    return {"id": user.id, "email": user.email, "role": user.role}

@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest):
    decoded = decode_token(payload.refresh_token)
    if decoded is None or decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh inválido")
    access = create_access_token(decoded["sub"])
    return TokenResponse(access_token=access)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user
