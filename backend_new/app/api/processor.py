"""Shared text pipeline for REST + WebSocket handlers.

process_text takes the FastAPI app (for its .state.ctx) and returns the
WS-shaped result dict. Social intents route to chat; everything else is a
skill execution.
"""

from typing import Any, Dict

from app.core.skill_registry import SkillRegistry

SOCIAL_INTENTS = {"greeting", "thanks", "goodbye", "joke"}


async def process_text(app, text: str) -> Dict[str, Any]:
    ctx = app.state.ctx
    parsed = await ctx.nlu.process(text)
    intent = parsed["intent"]
    params = parsed["params"]

    if intent in SOCIAL_INTENTS or intent == "chat":
        reply = await ctx.chat.chat(text)
        return {
            "intent": intent, "params": params, "source": parsed["source"],
            "confidence": parsed["confidence"], "success": True,
            "narration": reply, "command_type": "chat",
        }

    if intent == "teach_skill":
        return {
            "intent": intent, "params": params, "source": parsed["source"],
            "confidence": parsed["confidence"], "success": True,
            "narration": "Tell me the intent and I'll learn it. Use /teach {text, intent}.",
            "command_type": "chat",
        }

    result = await ctx.kernel.execute_intent(intent, params, ctx)
    return {
        "intent": intent, "params": params, "source": parsed["source"],
        "confidence": parsed["confidence"],
        "success": result.get("success", False),
        "narration": result.get("narration", "Command processed."),
        "command_type": "skill",
        "data": result.get("data"),
    }
