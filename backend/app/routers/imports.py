from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.imports import ImportReport
from app.services.csv_import import Entity, build_template, import_csv

router = APIRouter(prefix="/imports", tags=["imports"])


def _authorize(entidad: Entity, user: User) -> None:
    if entidad == "usuarios":
        if user.role not in ("admin", "coordinador"):
            raise HTTPException(status_code=403, detail="Rol no autorizado para importar usuarios.")
        return
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Rol no autorizado para esta importación.")


@router.post("/{entidad}", response_model=ImportReport)
async def import_entity(
    entidad: Entity,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
) -> ImportReport:
    _authorize(entidad, user)
    return await import_csv(entidad, file, db, user)


@router.get("/{entidad}/template")
async def download_template(
    entidad: Entity,
    user: User = Depends(get_current_user),
) -> Response:
    _authorize(entidad, user)
    content = build_template(entidad)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="plantilla-{entidad}.csv"',
        },
    )
