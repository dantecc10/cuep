from fastapi import Response

from app.core.config import settings


def _cookie_options() -> dict:
    options = {
        "key": settings.REFRESH_COOKIE_NAME,
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": settings.REFRESH_COOKIE_PATH,
        "max_age": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    }
    if settings.COOKIE_DOMAIN:
        options["domain"] = settings.COOKIE_DOMAIN
    return options


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(value=token, **_cookie_options())


def clear_refresh_cookie(response: Response) -> None:
    options = _cookie_options()
    options.pop("max_age", None)
    response.delete_cookie(**options)
