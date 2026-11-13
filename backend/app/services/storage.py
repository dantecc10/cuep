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


def r2_configured() -> bool:
    return bool(
        settings.R2_ACCOUNT_ID
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_SECRET_ACCESS_KEY
        and settings.R2_BUCKET
    )


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
