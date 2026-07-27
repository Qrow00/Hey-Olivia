from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.system_config import system_config_service

router = APIRouter()


class ConfigUpdate(BaseModel):
    tier: Optional[str] = None
    models: Optional[dict] = None
    features: Optional[dict] = None
    intervals: Optional[dict] = None
    limits: Optional[dict] = None


@router.get("/specs")
async def get_specs():
    specs = system_config_service.detect_specs()
    recommended_tier = system_config_service.recommend_tier(specs)
    preset = system_config_service.get_preset(recommended_tier)

    return {
        "specs": specs,
        "recommended_tier": recommended_tier,
        "preset": preset,
    }


@router.get("/config")
async def get_config():
    return system_config_service.get_active_config()


@router.post("/config")
async def update_config(update: ConfigUpdate):
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    return system_config_service.update_config(updates)


@router.post("/config/apply")
async def apply_tier(tier: str = "medium"):
    if tier not in ("low", "medium", "high"):
        return {"error": f"Invalid tier: {tier}. Must be low, medium, or high."}
    return system_config_service.apply_tier(tier)


@router.get("/models")
async def get_models():
    return system_config_service.get_available_models()


@router.get("/health")
async def health():
    specs = system_config_service.detect_specs()
    tier = system_config_service.recommend_tier(specs)
    return {
        "status": "online",
        "tier": tier,
        "ram_gb": specs["ram_gb"],
        "has_gpu": specs["gpu"]["has_gpu"],
        "cpu_count": specs["cpu_count"],
    }
