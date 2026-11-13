from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.student import Student
from app.models.user import User
from app.services.storage import upload_avatar

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    url = await upload_avatar(file, user.id)
    user.foto_url = url
    if user.role == "alumno":
        result = await db.execute(select(Student).where(Student.user_id == user.id))
        student = result.scalar_one_or_none()
        if student is not None:
            student.photo_url = url
    await db.flush()
    return {"url": url, "foto_url": url}
