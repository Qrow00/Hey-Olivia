"""J.A.R.V.I.S. V4 (Agent Core) - FastAPI application entry point.

Replaces V3's main_new.py:
  - LLM-free NLU command path (regex -> classifier -> chat)
  - Chat model (llama-server / GGUF / fallback) for conversation only
  - Personality sliders, skills registry, memory, learner, vision
  - Same WebSocket transport as V3 plus new message types
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Config
from app.core.agent_kernel import AgentKernel
from app.state_store import StateStore
from app.nlu.pipeline import NLUPipeline
from app.chat.personality import Personality
from app.chat.chat_client import ChatClient
from app.skills import register_all
from app.api.processor import process_text

VERSION = "4.0.0"


@dataclass
class AgentContext:
    """Shared runtime context passed to skills and WS handlers."""

    cfg: Config
    kernel: AgentKernel
    personality: Personality
    nlu: NLUPipeline
    chat: ChatClient
    profile: Any
    state_store: Optional[StateStore] = None


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        print("J.A.R.V.I.S. V4 starting up...")
        cfg = Config()
        cfg.ensure_dirs()

        state_store = StateStore(db_path=cfg.db_path, data_dir=str(cfg.data_dir))

        kernel = AgentKernel(cfg)
        register_all(kernel.registry)
        await kernel.startup(state_store)

        personality = Personality(state_store, cfg.profile)
        profile = kernel.get_service("profile")
        nlu = NLUPipeline()
        chat = ChatClient(cfg, personality)

        app.state.ctx = AgentContext(
            cfg=cfg, kernel=kernel, personality=personality,
            nlu=nlu, chat=chat, profile=profile, state_store=state_store,
        )
        print(f"J.A.R.V.I.S. V4 ready. {len(kernel.registry.names())} skills registered.")

        from app.api.ws import manager
        from app.skills.scheduler import scheduler_watchdog

        watchdog = asyncio.create_task(
            scheduler_watchdog(app.state.ctx, manager, poll_seconds=20)
        )

        try:
            yield
        finally:
            watchdog.cancel()
            ctx = app.state.ctx
            if ctx is not None:
                await ctx.kernel.shutdown()
            print("J.A.R.V.I.S. V4 shutdown complete")

    app = FastAPI(title="J.A.R.V.I.S. V4 - Agent Core", version=VERSION, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.ctx: Optional[AgentContext] = None

    # --- shared processing -------------------------------------------------

    async def _process_text(text: str) -> Dict[str, Any]:
        """One-arg wrapper around the shared processor (bound to this app)."""
        return await process_text(app, text)

    # --- REST routes -------------------------------------------------------

    from app.api.routes import build_router

    app.include_router(build_router(_process_text), prefix="")

    # --- WebSocket ---------------------------------------------------------

    from app.api.ws import ws_endpoint

    app.add_api_websocket_route("/ws", ws_endpoint)

    # --- static web frontend (registered last; API routes take precedence) ---

    from fastapi.staticfiles import StaticFiles
    from app.config import BASE_DIR

    web_dir = BASE_DIR / "web"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

    return app


app = create_app()
