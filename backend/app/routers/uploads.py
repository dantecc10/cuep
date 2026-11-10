from fastapi import APIRouter, Depends, File, UploadFile

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.storage import upload_avatar

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    url = await upload_avatar(file, user.id)
    return {"url": url}
