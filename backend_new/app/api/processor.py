"""Shared text pipeline for REST + WebSocket handlers.

process_text takes the FastAPI app (for its .state.ctx) and returns the
WS-shaped result dict. Social intents route to chat; everything else is a
skill execution. A short per-process conversation ring keeps recent turns
so the chat model has context.
"""

import asyncio
from collections import deque
from typing import Any, Dict

from app.core.skill_registry import SkillRegistry

SOCIAL_INTENTS = {"greeting", "thanks", "goodbye", "joke"}

_HISTORY: "deque[Dict[str, str]]" = deque(maxlen=64)


async def process_text(app, text: str) -> Dict[str, Any]:
    ctx = app.state.ctx
    parsed = await ctx.nlu.process(text)
    intent = parsed["intent"]
    params = parsed["params"]

    if intent in SOCIAL_INTENTS or intent == "chat":
        history = list(_HISTORY)[-ctx.cfg.conv_history_size:]
        reply = await ctx.chat.chat(text, history=history)
        _record(text, reply)
        result = {
            "intent": intent, "params": params, "source": parsed["source"],
            "confidence": parsed["confidence"], "success": True,
            "narration": reply, "command_type": "chat",
        }
        await _maybe_learn(ctx, text, result)
        return result

    if intent == "teach_skill":
        reply = "Tell me the intent and I'll learn it. Use /teach {text, intent}."
        _record(text, reply)
        result = {
            "intent": intent, "params": params, "source": parsed["source"],
            "confidence": parsed["confidence"], "success": True,
            "narration": reply,
            "command_type": "chat",
        }
        await _maybe_learn(ctx, text, result)
        return result

    result = await ctx.kernel.execute_intent(intent, params, ctx)
    narration = result.get("narration", "Command processed.")
    _record(text, narration)
    out = {
        "intent": intent, "params": params, "source": parsed["source"],
        "confidence": parsed["confidence"],
        "success": result.get("success", False),
        "narration": narration,
        "command_type": "skill",
        "data": result.get("data"),
    }
    await _maybe_learn(ctx, text, out)
    return out


async def _maybe_learn(ctx: Any, text: str, result: Dict[str, Any]) -> None:
    learner = getattr(ctx, "learner", None)
    if learner is not None:
        try:
            await learner.note(text, result)
        except Exception as e:
            print(f"[Learner] note error: {e}")


def _record(user_text: str, narration: str) -> None:
    _HISTORY.append({"role": "user", "text": user_text})
    _HISTORY.append({"role": "assistant", "text": narration})


def clear_history() -> None:
    _HISTORY.clear()
