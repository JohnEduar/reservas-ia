from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("", summary="Health check")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}
