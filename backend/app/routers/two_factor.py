import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as _delete

from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.core.limiter import limiter
from app.core.cookies import set_refresh_cookie
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_recovery_code,
    generate_totp_secret,
    hash_recovery_code,
    verify_password as verify_recovery_code,
    totp_provisioning_uri,
    verify_totp,
)
from app.models.user import User
from app.models.two_factor import (
    RecoveryCode,
    TrustedDevice,
    TwoFactorAuditLog,
    TwoFactorChallenge,
)
from app.services.email import EMAIL_FAILED, send_email_sync
from fastapi.concurrency import run_in_threadpool
from app.schemas.two_factor import (
    ChallengeResponse,
    RecoveryCodesResponse,
    ResendRequest,
    TOTPEnrollResponse,
    TOTPVerifyRequest,
    Verify2FARequest,
)

router = APIRouter(prefix="/auth/2fa", tags=["2fa"])


def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


async def _audit(db: AsyncSession, user_id: int, method: str, success: bool, ip: str | None):
    db.add(TwoFactorAuditLog(user_id=user_id, method=method, success=success, ip_address=ip))
    await db.flush()


@router.post("/totp/enroll", response_model=TOTPEnrollResponse)
async def totp_enroll(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    secret = generate_totp_secret()
    user.totp_secret = encrypt_totp_secret(secret)
    user.totp_enabled = False
    await db.flush()
    uri = totp_provisioning_uri(secret, user.email)
    return TOTPEnrollResponse(provisioning_uri=uri, secret=secret)


@router.post("/totp/verify", response_model=RecoveryCodesResponse)
async def totp_verify(payload: TOTPVerifyRequest, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP no enrolado")
    secret = decrypt_totp_secret(user.totp_secret)
    if not verify_totp(secret, payload.code):
        await _audit(db, user.id, "totp", False, request.client.host if request.client else None)
        raise HTTPException(status_code=400, detail="Código inválido")
    user.totp_enabled = True
    # generate recovery codes
    codes = [generate_recovery_code() for _ in range(10)]
    for c in codes:
        db.add(RecoveryCode(user_id=user.id, code_hash=hash_recovery_code(c)))
    await db.flush()
    await _audit(db, user.id, "totp", True, request.client.host if request.client else None)
    return RecoveryCodesResponse(recovery_codes=codes)


@router.post("/totp/disable", status_code=204)
async def totp_disable(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    user.totp_secret = None
    user.totp_enabled = False
    await db.execute(_delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
    await db.flush()
    return None


@router.post("/challenge", response_model=ChallengeResponse)
@limiter.limit("5/minute")
async def create_challenge(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    # generate 6-digit code
    code = f"{secrets.randbelow(1000000):06d}"
    challenge_id = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    ch = TwoFactorChallenge(
        user_id=user.id,
        challenge_id=challenge_id,
        otp_hash=_hash_otp(code),
        expires_at=expires_at,
    )
    db.add(ch)
    await db.flush()
    # send email always
    email_status = await run_in_threadpool(send_email_sync, user.email, "Código de verificación CUEP", f"Tu código de verificación es: {code}\nExpira en 10 minutos.")
    if email_status == EMAIL_FAILED:
        raise HTTPException(
            status_code=503,
            detail="No se pudo enviar el código por correo. Revisa la configuración SMTP del servidor.",
        )
    methods = ["email"]
    if user.totp_enabled:
        methods.append("totp")
    return ChallengeResponse(challenge_id=challenge_id, expires_at=expires_at.isoformat(), methods=methods)


@router.post("/resend", response_model=ChallengeResponse)
@limiter.limit("5/minute")
async def resend(request: Request, payload: ResendRequest, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(TwoFactorChallenge).where(TwoFactorChallenge.challenge_id == payload.challenge_id))
    ch = result.scalar_one_or_none()
    if ch is None or ch.consumed or ch.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Challenge inválido o expirado")
    user = await db.get(User, ch.user_id)
    code = f"{secrets.randbelow(1000000):06d}"
    ch.otp_hash = _hash_otp(code)
    ch.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    ch.attempts = 0
    await db.flush()
    email_status = await run_in_threadpool(send_email_sync, user.email, "Código de verificación CUEP", f"Tu código de verificación es: {code}\nExpira en 10 minutos.")
    if email_status == EMAIL_FAILED:
        raise HTTPException(
            status_code=503,
            detail="No se pudo enviar el código por correo. Revisa la configuración SMTP del servidor.",
        )
    methods = ["email"]
    if user.totp_enabled:
        methods.append("totp")
    return ChallengeResponse(challenge_id=ch.challenge_id, expires_at=ch.expires_at.isoformat(), methods=methods)


@router.post("/verify")
@limiter.limit("10/minute")
async def verify_2fa(request: Request, response: Response, payload: Verify2FARequest, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(TwoFactorChallenge).where(TwoFactorChallenge.challenge_id == payload.challenge_id))
    ch = result.scalar_one_or_none()
    if ch is None or ch.consumed:
        raise HTTPException(status_code=400, detail="Challenge inválido")
    if ch.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Challenge expirado")
    if ch.attempts >= 5:
        raise HTTPException(status_code=429, detail="Demasiados intentos")
    user = await db.get(User, ch.user_id)
    ch.attempts += 1
    code = payload.code.strip()
    success = False
    method = "email"
    # email OTP
    if _hash_otp(code) == ch.otp_hash:
        success = True
        method = "email"
    # TOTP
    elif user.totp_enabled and user.totp_secret:
        secret = decrypt_totp_secret(user.totp_secret)
        if verify_totp(secret, code):
            success = True
            method = "totp"
    # recovery code
    if not success:
        rc_result = await db.execute(select(RecoveryCode).where(RecoveryCode.user_id == user.id, not RecoveryCode.used))
        for rc in rc_result.scalars().all():
            if verify_recovery_code(code, rc.code_hash):
                rc.used = True
                success = True
                method = "recovery_code"
                break
    await db.flush()
    if not success:
        await _audit(db, user.id, method, False, request.client.host if request.client else None)
        raise HTTPException(status_code=400, detail="Código inválido")
    ch.consumed = True
    await db.flush()
    # trusted device
    if payload.trust_device:
        token = secrets.token_urlsafe(32)
        td = TrustedDevice(user_id=user.id, token_hash=hashlib.sha256(token.encode()).hexdigest(), expires_at=datetime.now(timezone.utc) + timedelta(days=30))
        db.add(td)
        await db.flush()
    await _audit(db, user.id, method, True, request.client.host if request.client else None)
    access = create_access_token(str(user.id))
    set_refresh_cookie(response, create_refresh_token(str(user.id)))
    return {"access_token": access, "token_type": "bearer", "trusted_device_token": token if payload.trust_device else None}
