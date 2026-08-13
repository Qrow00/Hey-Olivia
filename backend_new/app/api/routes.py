"""REST routes for J.A.R.V.I.S. V3."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import BASE_DIR, PERSONALITY_SLIDERS


def _check_token(request: Request) -> None:
    """Reject unauthenticated API calls when JARVIS_TOKEN is configured."""
    if request.url.path in ("/", "/health"):
        return
    ctx = getattr(request.app.state, "ctx", None)
    token = getattr(ctx.cfg, "access_token", "") if ctx is not None else ""
    if not token:
        return
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        provided = auth.split(" ", 1)[1].strip()
    else:
        provided = request.query_params.get("token", "")
    if provided != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


def build_router(process_text) -> APIRouter:
    router = APIRouter(dependencies=[Depends(_check_token)])

    def _ctx(request: Request):
        return request.app.state.ctx

    @router.get("/")
    async def root(request: Request):
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            web = BASE_DIR / "web" / "index.html"
            if web.exists():
                return HTMLResponse(web.read_text(encoding="utf-8"))
        return {
            "name": "J.A.R.V.I.S. V3 - Agent Core",
            "version": "4.0.0",
            "status": "operational",
            "description": "LLM-free command pipeline + local chat model + skills",
        }

    @router.get("/health")
    async def health(request: Request):
        ctx = _ctx(request)
        return {
            "status": "healthy" if ctx is not None else "starting",
            "skills": len(ctx.kernel.registry.names()) if ctx else 0,
            "profile": ctx.cfg.profile if ctx else "default",
            "services": list(ctx.kernel.services.keys()) if ctx else [],
        }

    @router.get("/skills")
    async def skills(request: Request):
        ctx = _ctx(request)
        if ctx is None:
            return {"enabled": [], "all_registered": []}
        return {
            "enabled": ctx.kernel.registry.names(),
            "all_registered": ctx.kernel.registry.names(),
        }

    @router.get("/personality")
    async def get_personality(request: Request):
        ctx = _ctx(request)
        return ctx.personality.sliders() if ctx else {}

    @router.put("/personality")
    async def update_personality(request: Request, payload: Dict[str, float]):
        ctx = _ctx(request)
        if ctx is None:
            return {"error": "not ready"}
        return ctx.personality.set_many(payload)

    @router.post("/command")
    async def command(request: Request, payload: Dict[str, str]):
        ctx = _ctx(request)
        text = (payload.get("text") or "").strip()
        if not text:
            return {"intent": "chat", "success": False, "narration": "Empty command."}
        result = await process_text(text)
        result["text"] = text
        return result

    @router.post("/tts")
    async def tts(request: Request, payload: Dict[str, str]):
        ctx = _ctx(request)
        if ctx is None:
            return {"success": False, "audio_base64": "", "narration": "Not ready."}
        svc = ctx.kernel.get_service("tts")
        text = (payload.get("text") or "").strip()
        if svc is None or not svc.available():
            return {
                "success": False, "audio_base64": "", "voice": "unavailable",
                "narration": "TTS not available (install edge-tts or Kokoro and enable the voice service).",
            }
        import base64
        audio = await svc.synthesize(text, ctx.personality.tts_params())
        return {
            "success": bool(audio),
            "audio_base64": base64.b64encode(audio).decode() if audio else "",
            "voice": svc.info().get("voice"),
        }

    @router.get("/faces")
    async def list_faces(request: Request):
        ctx = _ctx(request)
        face_db = ctx.kernel.get_service("face_db") if ctx else None
        if face_db is None:
            return {"identities": [], "count": 0}
        return {"identities": face_db.identities(), "count": face_db.count()}

    @router.post("/faces")
    async def add_face(request: Request, payload: Dict[str, Any]):
        ctx = _ctx(request)
        face_db = ctx.kernel.get_service("face_db") if ctx else None
        if face_db is None:
            return {"success": False, "narration": "Vision service not enabled (JARVIS_SERVICES=vision)."}
        name = payload.get("name", "")
        embedding = payload.get("embedding")
        if not name or not embedding:
            return {"success": False, "narration": "Need both 'name' and 'embedding'."}
        face_db.add(name, embedding)
        return {"success": True, "narration": f"Learned face for {name}."}

    @router.post("/teach")
    async def teach(request: Request, payload: Dict[str, str]):
        ctx = _ctx(request)
        if ctx is None:
            return {"success": False}
        text, intent = payload.get("text", ""), payload.get("intent", "")
        ok = await ctx.nlu.teach(text, intent)
        if ok:
            store = ctx.kernel.get_service("feedback")
            if store is not None:
                await store.record(text, intent, "teach", note="explicit teach")
        return {"success": ok, "narration": f"Learned '{text}' -> {intent}." if ok else "Teach failed."}

    @router.post("/feedback")
    async def feedback(request: Request, payload: Dict[str, Any]):
        ctx = _ctx(request)
        store = ctx.kernel.get_service("feedback") if ctx else None
        if store is None:
            return {"success": False, "narration": "Learner service not enabled (JARVIS_SERVICES=learner)."}
        await store.record(
            payload.get("text", ""), payload.get("intent", "chat"),
            payload.get("rating", "good"), payload.get("note", ""),
            payload.get("correction", ""),
        )
        return {"success": True, "narration": "Feedback recorded."}

    @router.get("/schedule")
    async def get_schedule(request: Request):
        ctx = _ctx(request)
        if ctx is None or ctx.state_store is None:
            return {"items": []}
        items = ctx.state_store.get(ctx.cfg.profile, "scheduler.items", []) or []
        return {"items": items, "count": len(items)}

    @router.post("/schedule/clear")
    async def clear_schedule(request: Request):
        ctx = _ctx(request)
        if ctx is None or ctx.state_store is None:
            return {"success": False}
        ctx.state_store.set(ctx.cfg.profile, "scheduler.items", [])
        return {"success": True, "narration": "All reminders and alarms cleared."}

    @router.get("/model/status")
    async def model_status(request: Request):
        ctx = _ctx(request)
        if ctx is None:
            return {"chat_backend": "starting"}
        backend = "llama-server" if ctx.cfg.chat_use_llama_server else (
            "gguf" if ctx.chat._gguf_available() is not False else "fallback")
        return {
            "chat_backend": backend,
            "llama_server": ctx.cfg.chat_use_llama_server,
            "gguf_path": ctx.cfg.chat_gguf_path,
        }

    return router
