import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    devices, conversations, settings, commands, websocket, voice,
    screen_share, cameras, wearables, smart_home, vision, plugins,
    personality, voice_profiles, browser, system, auth,
)
from app.models.database import engine, Base

app = FastAPI(title="J.A.R.V.I.S. API", version="2.0.0")

JARVIS_SERVICES = os.getenv("JARVIS_SERVICES", "all").lower()
_services = JARVIS_SERVICES.split(",")

def service_enabled(name: str) -> bool:
    return "all" in _services or name in _services

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
app.include_router(browser.router, prefix="/api/v1/browser", tags=["browser"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])


def _startup_log(msg: str):
    print(f"[STARTUP] {msg}", flush=True)


@app.on_event("startup")
async def startup():
    # First import of torch._C (libtorch DLL chain) can segfault on the main
    # thread when run concurrently with the subprocess/socket threads spawned
    # later in startup. Preload it here while the process is still quiet.
    try:
        import torch  # noqa: F401
    except Exception as e:
        print(f"[PRELOAD] torch unavailable: {e}", flush=True)

    _startup_log("database init...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from sqlalchemy import text
        try:
            await conn.execute(text("ALTER TABLE wearable_devices ADD COLUMN user_id VARCHAR DEFAULT 'default'"))
        except:
            pass
    _startup_log("database ok")

    if service_enabled("plugins"):
        from app.plugins.manager import plugin_manager
        from app.plugins.motion_detector import MotionDetectorPlugin
        await plugin_manager.register_plugin(MotionDetectorPlugin())
    _startup_log("plugins ok")

    if service_enabled("browser"):
        from app.services.hermes_browser import hermes_browser

        async def _init_browser():
            try:
                await hermes_browser.initialize()
            except Exception as e:
                print(f"[HERMES BROWSER] Init deferred: {e}")

        asyncio.create_task(_init_browser())

    if service_enabled("monitoring"):
        _startup_log("monitoring start...")
        from app.services.monitoring_service import monitoring_service
        from app.services.activity_logger import activity_logger
        await monitoring_service.start_polling()
        await activity_logger.start_polling()
        _startup_log("monitoring ok")

        from app.routers.websocket import _setup_monitoring_broadcast
        _setup_monitoring_broadcast()

    _startup_log("wearable load...")
    from app.services.wearable_service import wearable_service
    await wearable_service.load_from_db()
    _startup_log("wearable ok")

    from app.services.system_config import system_config_service
    asyncio.create_task(asyncio.to_thread(system_config_service.auto_adapt))

    from app.services.voice_service import voice_service
    asyncio.create_task(voice_service.initialize())

    from app.services.thermal_logger_service import thermal_logger_service
    thermal_logger_service.start()

    _startup_log(f"J.A.R.V.I.S. v2.0.0 initialized — services=[{JARVIS_SERVICES}]")


@app.on_event("shutdown")
async def shutdown():
    from app.services.conversation_memory import conversation_memory
    conversation_memory.save_on_exit()

    if service_enabled("browser"):
        from app.services.hermes_browser import hermes_browser
        await hermes_browser.shutdown()

    if service_enabled("monitoring"):
        from app.services.monitoring_service import monitoring_service
        from app.services.activity_logger import activity_logger
        await monitoring_service.stop_polling()
        await activity_logger.stop_polling()

    from app.services.thermal_logger_service import thermal_logger_service
    thermal_logger_service.stop()

    print("J.A.R.V.I.S. shutdown — memory saved")


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
            "browser": "/api/v1/browser",
            "system": "/api/v1/system",
            "monitoring": "ws://.../ws (type: monitoring_snapshot)",
        },
    }
