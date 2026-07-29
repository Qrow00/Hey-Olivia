from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.services.settings_service import settings_service
from app.dependencies import require_auth

router = APIRouter()


class SettingsUpdate(BaseModel):
    voice: Optional[dict] = None
    ui: Optional[dict] = None
    health: Optional[dict] = None
    smart_home: Optional[dict] = None


@router.get("")
async def get_settings(profile_id: str = Depends(require_auth)):
    return settings_service.get_all(profile_id)


@router.get("/noauth")
async def get_settings_public():
    return settings_service.get_all("default")


@router.put("")
async def update_settings(settings: SettingsUpdate, profile_id: str = Depends(require_auth)):
    updates = {k: v for k, v in settings.model_dump().items() if v is not None}
    updated = settings_service.update(profile_id, updates)
    return {"status": "updated", "settings": updated}


@router.patch("")
async def patch_settings(settings: SettingsUpdate, profile_id: str = Depends(require_auth)):
    updates = {k: v for k, v in settings.model_dump().items() if v is not None}
    updated = settings_service.update(profile_id, updates)
    return {"status": "patched", "settings": updated}


@router.post("/reset")
async def reset_settings(profile_id: str = Depends(require_auth)):
    defaults = settings_service.reset(profile_id)
    return {"status": "reset", "settings": defaults}
