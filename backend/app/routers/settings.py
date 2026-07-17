from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_settings():
    return {"theme": "dark", "language": "en", "voice_enabled": True}


@router.put("/")
async def update_settings(settings: dict):
    return {"status": "updated", "settings": settings}
