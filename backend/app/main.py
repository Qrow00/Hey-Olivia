from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import devices, conversations, settings, commands, websocket
from app.models.database import engine, Base

app = FastAPI(title="J.A.R.V.I.S. API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(commands.router, prefix="/api/commands", tags=["commands"])
app.include_router(websocket.router, tags=["websocket"])


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"name": "J.A.R.V.I.S.", "version": "0.1.0", "status": "online"}
