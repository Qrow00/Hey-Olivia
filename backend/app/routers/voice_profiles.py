from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.voice_profile_service import voice_profile_service

router = APIRouter()


class ProfileCreate(BaseModel):
    id: str
    name: str
    voice: str
    rate: int = 0
    pitch: int = 0
    description: str = ""


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    voice: Optional[str] = None
    rate: Optional[int] = None
    pitch: Optional[int] = None
    description: Optional[str] = None


class ActivateProfile(BaseModel):
    profile_id: str


@router.get("/")
async def list_profiles():
    return voice_profile_service.list_profiles()


@router.get("/active")
async def get_active_profile():
    return voice_profile_service.get_active_profile().id


@router.post("/active")
async def set_active_profile(data: ActivateProfile):
    return voice_profile_service.set_active(data.profile_id)


@router.post("/")
async def create_profile(data: ProfileCreate):
    return voice_profile_service.create_profile(
        data.id, data.name, data.voice, data.rate, data.pitch, data.description
    )


@router.put("/{profile_id}")
async def update_profile(profile_id: str, data: ProfileUpdate):
    updates = {k: v for k, v in data.dict().items() if v is not None}
    return voice_profile_service.update_profile(profile_id, **updates)


@router.delete("/{profile_id}")
async def delete_profile(profile_id: str):
    return voice_profile_service.delete_profile(profile_id)


@router.get("/{profile_id}/tts-config")
async def get_tts_config(profile_id: str):
    return voice_profile_service.get_edge_tts_config(profile_id)
