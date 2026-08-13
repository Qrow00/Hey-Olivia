"""RED/GREEN tests for JARVIS V4 skill registry."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_register_and_get():
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()

    @reg.skill("test_echo", description="echoes params")
    async def echo(params, ctx):
        return {"success": True, "narration": params.get("text", "")}

    assert "test_echo" in reg.names()
    assert reg.get("test_echo").description == "echoes params"


def test_execute_async():
    import asyncio
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()

    @reg.skill("test_add")
    async def add(params, ctx):
        return {"success": True, "narration": str(params["a"] + params["b"])}

    result = asyncio.run(reg.execute("test_add", {"a": 1, "b": 2}))
    assert result["success"] is True
    assert result["narration"] == "3"


def test_execute_unknown_skill():
    import asyncio
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    result = asyncio.run(reg.execute("nope", {}))
    assert result["success"] is False
    assert "not registered" in result["narration"]


def test_execute_raises_is_graceful():
    import asyncio
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()

    @reg.skill("test_broken")
    async def broken(params, ctx):
        raise RuntimeError("boom")

    result = asyncio.run(reg.execute("test_broken", {}))
    assert result["success"] is False
    assert "boom" in result["error"]


def test_sync_function_supported():
    import asyncio
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()

    @reg.skill("test_sync")
    def sync_fn(params, ctx):
        return {"success": True, "narration": "sync ok"}

    result = asyncio.run(reg.execute("test_sync", {}))
    assert result["narration"] == "sync ok"


def test_set_enabled():
    import asyncio
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()

    @reg.skill("test_toggle")
    async def toggled(params, ctx):
        return {"success": True}

    reg.set_enabled("test_toggle", False)
    result = asyncio.run(reg.execute("test_toggle", {}))
    assert result["success"] is False
    assert "disabled" in result["narration"]
