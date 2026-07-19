from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    devices, conversations, settings, commands, websocket, voice,
    screen_share, cameras, wearables, smart_home, vision, plugins,
    personality, voice_profiles,
)
from app.models.database import engine, Base
from app.plugins.manager import plugin_manager
from app.plugins.motion_detector import MotionDetectorPlugin

app = FastAPI(title="J.A.R.V.I.S. API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(commands.router, prefix="/api/v1/commands", tags=["commands"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
app.include_router(screen_share.router, prefix="/api/v1/screen", tags=["screen-share"])
app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["cameras"])
app.include_router(wearables.router, prefix="/api/v1/wearables", tags=["wearables"])
app.include_router(smart_home.router, prefix="/api/v1/smart-home", tags=["smart-home"])
app.include_router(vision.router, prefix="/api/v1/vision", tags=["vision"])
app.include_router(plugins.router, prefix="/api/v1/plugins", tags=["plugins"])
app.include_router(personality.router, prefix="/api/v1/personality", tags=["personality"])
app.include_router(voice_profiles.router, prefix="/api/v1/voice-profiles", tags=["voice-profiles"])


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await plugin_manager.register_plugin(MotionDetectorPlugin())

    print("J.A.R.V.I.S. v2.0.0 initialized")


@app.get("/")
async def root():
    return {
        "name": "J.A.R.V.I.S.",
        "version": "2.0.0",
        "status": "online",
        "api_version": "v1",
    }


@app.get("/api/v1")
async def api_root():
    return {
        "version": "v1",
        "endpoints": {
            "devices": "/api/v1/devices",
            "conversations": "/api/v1/conversations",
            "settings": "/api/v1/settings",
            "commands": "/api/v1/commands",
            "voice": "/api/v1/voice",
            "screen": "/api/v1/screen",
            "cameras": "/api/v1/cameras",
            "wearables": "/api/v1/wearables",
            "smart-home": "/api/v1/smart-home",
            "vision": "/api/v1/vision",
            "plugins": "/api/v1/plugins",
            "personality": "/api/v1/personality",
            "voice-profiles": "/api/v1/voice-profiles",
        },
    }
