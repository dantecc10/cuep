from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.metrics import build_metrics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
async def dashboard_metrics(
    desde: date | None = None,
    hasta: date | None = None,
    sede_id: int | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    try:
        return await build_metrics(db, user, desde, hasta, sede_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
