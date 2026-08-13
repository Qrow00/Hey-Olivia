"""RED/GREEN tests for JARVIS V4 skills."""
import sys
import os
import asyncio
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


def _ctx():
    class Ctx:
        kernel = None
        personality = None
    return Ctx()


def test_system_time_skill():
    from app.skills.system import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("info_time", {}, _ctx()))
    assert result["success"] is True
    assert "time" in result["narration"].lower()


def test_system_date_skill():
    from app.skills.system import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("info_date", {}, _ctx()))
    assert result["success"] is True


def test_email_skill_no_config():
    """Email skill should report graceful failure without credentials."""
    from app.skills.email import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("email_read", {}, _ctx()))
    assert result["success"] is False
    assert "configure" in result["narration"].lower()


def test_media_youtube_skill():
    from app.skills.media import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("browser_youtube", {"query": "iron man trailer"}, _ctx()))
    assert result["success"] is True
    assert "youtube.com" in result.get("data", {}).get("url", "")


def test_code_scaffold_skill():
    from app.skills.code import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("code_scaffold", {"language": "python"}, _ctx()))
    assert result["success"] is True
    assert "app.py" in result.get("narration", "")


def test_smart_home_skill_offline():
    """Smart home skill should work offline (device recorded) without MQTT."""
    from app.skills.smart_home import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("smart_home_turn_on", {"device": "kitchen lights"}, _ctx()))
    assert result["success"] is True
    assert "kitchen lights" in result["narration"]


def test_uptime_skill():
    from app.skills.system import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("info_uptime", {}, _ctx()))
    assert result["success"] is True
    assert result.get("data", {}).get("uptime_seconds", 0) > 0


def test_scheduler_reminder_skill():
    """Reminder persists to state store so JARVIS can act on it later."""
    import tempfile
    from app.state_store import StateStore
    from app.skills.scheduler import register
    from app.core.skill_registry import SkillRegistry

    class Ctx:
        state_store = StateStore(db_path=os.path.join(tempfile.mkdtemp(), "s.db"),
                                 data_dir=os.path.join(tempfile.mkdtemp(), "d"))
        profile = "default"

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("scheduler_reminder", {"task": "call mom"}, Ctx()))
    assert result["success"] is True
    items = Ctx.state_store.get("default", "scheduler.items", [])
    assert any("call mom" in str(i) for i in items)


def test_scheduler_reminder_uses_cfg_profile():
    """Regression: AgentContext.profile is a ProfileStore object, not a name."""
    import tempfile
    from app.state_store import StateStore
    from app.skills.scheduler import register
    from app.core.skill_registry import SkillRegistry

    class Cfg:
        profile = "alice"

    class Ctx:
        state_store = StateStore(db_path=os.path.join(tempfile.mkdtemp(), "s.db"),
                                 data_dir=os.path.join(tempfile.mkdtemp(), "d"))
        profile = object()
        cfg = Cfg()

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("scheduler_reminder", {"task": "take the bins out"}, Ctx()))
    assert result["success"] is True
    assert Ctx.state_store.get("alice", "scheduler.items", []) != []


def test_scheduler_alarm_skill():
    import tempfile
    from app.state_store import StateStore
    from app.skills.scheduler import register
    from app.core.skill_registry import SkillRegistry

    class Ctx:
        state_store = StateStore(db_path=os.path.join(tempfile.mkdtemp(), "s.db"),
                                 data_dir=os.path.join(tempfile.mkdtemp(), "d"))
        profile = "default"

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("scheduler_alarm", {"time": "7:00 AM"}, Ctx()))
    assert result["success"] is True
    assert "7:00" in result["narration"]


def test_browser_youtube_open_alias():
    from app.skills.media import register
    from app.core.skill_registry import SkillRegistry

    reg = SkillRegistry()
    register(reg)
    result = asyncio.run(reg.execute("browser_youtube_open", {}, _ctx()))
    assert result["success"] is True
    assert "youtube.com" in result.get("data", {}).get("url", "")


def test_parse_alarm_time():
    import datetime
    from app.skills.scheduler import parse_alarm_time

    t = parse_alarm_time("7:00 AM")
    assert t is not None and t.hour == 7 and t.minute == 0
    t = parse_alarm_time("19:30")
    assert t is not None and t.hour == 19 and t.minute == 30
    t = parse_alarm_time("7 pm")
    assert t is not None and t.hour == 19
    assert parse_alarm_time("") is None
    assert parse_alarm_time("soon") is None


def test_due_items_marks_fired():
    import tempfile
    from app.state_store import StateStore
    from app.skills import scheduler
    from app.skills.scheduler import due_items

    class Cfg:
        profile = "default"

    class Ctx:
        state_store = StateStore(db_path=os.path.join(tempfile.mkdtemp(), "s.db"),
                                 data_dir=os.path.join(tempfile.mkdtemp(), "d"))
        cfg = Cfg()

    when = (datetime.datetime.now() - datetime.timedelta(seconds=30)).strftime("%I:%M %p")
    Ctx.state_store.set("default", scheduler._STORE_KEY,
                        [{"id": "a1", "kind": "alarm", "task": "wake up", "when": when, "done": False}])
    due = due_items(Ctx, grace_seconds=120)
    assert len(due) == 1 and due[0]["id"] == "a1"

    Ctx.state_store.set("default", scheduler._FIRED_KEY, ["a1"])
    assert due_items(Ctx, grace_seconds=120) == []


def test_due_items_ignores_far_future():
    import tempfile
    from app.state_store import StateStore
    from app.skills import scheduler
    from app.skills.scheduler import due_items

    class Cfg:
        profile = "default"

    class Ctx:
        state_store = StateStore(db_path=os.path.join(tempfile.mkdtemp(), "s.db"),
                                 data_dir=os.path.join(tempfile.mkdtemp(), "d"))
        cfg = Cfg()

    when = (datetime.datetime.now() + datetime.timedelta(hours=2)).strftime("%I:%M %p")
    Ctx.state_store.set("default", scheduler._STORE_KEY,
                        [{"id": "a2", "kind": "alarm", "task": "later", "when": when, "done": False}])
    assert due_items(Ctx) == []


def test_routes_require_token():
    """REST API returns 401 when JARVIS_TOKEN is set and not provided."""
    import importlib
    import os
    from fastapi.testclient import TestClient

    os.environ["JARVIS_TOKEN"] = "secret"
    try:
        from app.api.main import create_app
        test_app = create_app()
        with TestClient(test_app) as client:
            resp = client.post("/command", json={"text": "what time is it"})
            assert resp.status_code == 401
            resp = client.post("/command", json={"text": "what time is it"},
                               headers={"Authorization": "Bearer secret"})
            assert resp.status_code == 200
            resp = client.get("/health")
            assert resp.status_code == 200
    finally:
        os.environ.pop("JARVIS_TOKEN", None)
