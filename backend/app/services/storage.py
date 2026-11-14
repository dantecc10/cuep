import logging
import uuid

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_AVATAR_BYTES = 5 * 1024 * 1024


def log_r2_config() -> None:
    if not r2_credentials_configured():
        logger.info("R2 no configurado; las fotos usaran una URL publica.")
        return
    logger.info(
        "R2 config: endpoint=%s bucket=%s key_suffix=%s secret_len=%d public_base=%s",
        settings.r2_endpoint_url,
        settings.R2_BUCKET or "<sin configurar>",
        settings.R2_ACCESS_KEY_ID[-6:],
        len(settings.R2_SECRET_ACCESS_KEY),
        settings.R2_PUBLIC_BASE or "<sin configurar>",
    )
    if settings.R2_PUBLIC_BASE.rstrip("/").endswith("r2.cloudflarestorage.com"):
        logger.warning(
            "R2_PUBLIC_BASE apunta al endpoint privado S3; "
            "usa la URL publica r2.dev o un dominio personalizado."
        )
    if not settings.R2_PRIVATE_BUCKET:
        logger.warning(
            "R2_PRIVATE_BUCKET sin configurar: la subida de comprobantes de pago "
            "respondera 503 y no se podran validar transferencias con imagen."
        )
    elif settings.R2_PRIVATE_BUCKET == settings.R2_BUCKET:
        logger.warning(
            "R2_PRIVATE_BUCKET es igual a R2_BUCKET: los comprobantes de pago "
            "quedarian en el bucket publico. Usa un bucket privado aparte."
        )
    else:
        logger.info(
            "R2 privado: bucket=%s (comprobantes de pago, solo URLs firmadas)",
            settings.R2_PRIVATE_BUCKET,
        )


def r2_credentials_configured() -> bool:
    return bool(
        settings.R2_ACCOUNT_ID
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
    )


def r2_configured() -> bool:
    return bool(r2_credentials_configured() and settings.R2_BUCKET)


def _public_url(key: str) -> str:
    base = settings.R2_PUBLIC_BASE.rstrip("/")
    if base:
        return f"{base}/{key}"
    return f"https://{settings.R2_ACCOUNT_ID}.r2.dev/{key}"


async def upload_avatar(file: UploadFile, user_id: int) -> str:
    if not r2_configured():
        raise HTTPException(
            status_code=503,
            detail="R2 no configurado. Usa una URL pública para tu foto.",
        )

    content_type = file.content_type or ""
    extension = ALLOWED_IMAGE_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Usa JPG, PNG, WEBP o GIF.",
        )

    data = await file.read()
    if len(data) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=413,
            detail="La imagen no debe superar 5 MB.",
        )

    import boto3

    key = f"avatars/{user_id}/{uuid.uuid4().hex}{extension}"
    client = boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )

    def put() -> None:
        client.put_object(
            Bucket=settings.R2_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    try:
        await run_in_threadpool(put)
    except Exception as exc:
        logger.exception("Fallo al subir a R2 (bucket=%s)", settings.R2_BUCKET)
        code = None
        response = getattr(exc, "response", None)
        if isinstance(response, dict):
            code = response.get("Error", {}).get("Code")
        detail = "No se pudo subir la imagen. Intenta de nuevo o usa una URL pública."
        if code:
            detail = (
                f"No se pudo subir la imagen a R2 ({code}). "
                "Revisa el nombre del bucket, las credenciales y los permisos del token."
            )
        raise HTTPException(status_code=502, detail=detail) from exc

    return _public_url(key)


ALLOWED_PROOF_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def private_bucket() -> str:
    """Bucket privado de comprobantes. Nunca cae al bucket público."""
    if not settings.R2_PRIVATE_BUCKET:
        raise HTTPException(
            status_code=503,
            detail=(
                "Falta R2_PRIVATE_BUCKET: los comprobantes de pago requieren "
                "un bucket privado propio (no se usa el bucket público)."
            ),
        )
    return settings.R2_PRIVATE_BUCKET


def private_bucket_configured() -> bool:
    return bool(
        r2_credentials_configured()
        and settings.R2_PRIVATE_BUCKET
    )


def _s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


async def upload_payment_proof(
    file: UploadFile, student_id: int, pago_id: int
) -> dict[str, str | int]:
    bucket = private_bucket()
    if not r2_credentials_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "El almacenamiento privado no está configurado: faltan las "
                "credenciales de R2 en el servidor."
            ),
        )
    content_type = file.content_type or ""
    extension = ALLOWED_PROOF_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Usa PDF, JPG, PNG o WEBP.",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="El comprobante está vacío.")
    if len(data) > settings.PAYMENT_PROOF_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El comprobante no debe superar {settings.PAYMENT_PROOF_MAX_BYTES // (1024 * 1024)} MB.",
        )
    key = f"comprobantes/{student_id}/{pago_id}/{uuid.uuid4().hex}{extension}"
    client = _s3_client()

    def put() -> None:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    try:
        await run_in_threadpool(put)
    except Exception as exc:
        logger.exception("Fallo al subir comprobante a R2 privado")
        raise HTTPException(
            status_code=502,
            detail="No se pudo subir el comprobante. Intenta de nuevo.",
        ) from exc
    return {
        "key": key,
        "nombre": file.filename or f"comprobante{extension}",
        "content_type": content_type,
        "size": len(data),
    }


def presigned_payment_proof_url(key: str, expires_in: int = 900) -> str | None:
    if not private_bucket_configured():
        return None
    client = _s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_PRIVATE_BUCKET, "Key": key},
        ExpiresIn=expires_in,
    )
