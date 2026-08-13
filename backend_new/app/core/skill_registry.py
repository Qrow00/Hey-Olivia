"""SkillRegistry - maps intent names to executable skills.

A skill is a named capability with an async `execute(params, ctx) -> dict`.
Results follow the V3 handler convention: {success, narration, type, data}.
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional


@dataclass
class Skill:
    """A single executable capability of the agent."""

    name: str
    execute: Callable[[Dict[str, Any], Any], Awaitable[Dict[str, Any]]]
    description: str = ""
    patterns: List[str] = field(default_factory=list)
    enabled: bool = True


class SkillRegistry:
    """Registry of skills keyed by intent name."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register(
        self,
        name: str,
        fn: Optional[Callable] = None,
        *,
        description: str = "",
        patterns: Optional[List[str]] = None,
    ) -> Callable:
        """Register a skill. Usable as a plain call or decorator."""

        def _wrap(f):
            target = f
            if not inspect.iscoroutinefunction(f):
                async def wrapper(params, ctx=None):
                    res = target(params, ctx)
                    if inspect.isawaitable(res):
                        res = await res
                    return res

                wrapper.__name__ = f.__name__
                wrapper.__doc__ = f.__doc__
                f = wrapper
            self._skills[name] = Skill(
                name=name, execute=f, description=description or (f.__doc__ or "").strip(),
                patterns=list(patterns or []),
            )
            return f

        if fn is not None:
            return _wrap(fn)
        return _wrap

    def skill(self, name: str, fn: Optional[Callable] = None, **kw) -> Callable:
        """Register a skill; usable as `reg.skill("name", fn, description=...)`."""
        return self.register(name, fn, **kw)

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def all(self) -> Dict[str, Skill]:
        return dict(self._skills)

    def names(self) -> List[str]:
        return list(self._skills.keys())

    def set_enabled(self, name: str, enabled: bool) -> None:
        if name in self._skills:
            self._skills[name].enabled = enabled

    async def execute(self, name: str, params: Dict[str, Any], ctx: Any = None) -> Dict[str, Any]:
        """Execute a skill by intent name with graceful error handling."""
        skill = self._skills.get(name)
        if skill is None:
            return {"success": False, "narration": f"Skill '{name}' not registered.", "error": "unknown_skill", "type": "error"}
        if not skill.enabled:
            return {"success": False, "narration": f"Skill '{name}' is disabled.", "error": "disabled", "type": "error"}
        try:
            result = skill.execute(params, ctx)
            if asyncio.iscoroutine(result):
                result = await result
            if not isinstance(result, dict):
                result = {"success": True, "narration": str(result), "type": "skill_result"}
            result.setdefault("type", "skill_result")
            result.setdefault("handler", name)
            return result
        except Exception as e:
            return {
                "success": False,
                "narration": f"Error executing {name}: {e}",
                "error": str(e),
                "type": "error",
                "handler": name,
            }


registry = SkillRegistry()
