import pytest
from app.services.command_registry import CommandRegistry


def test_parse_time_command():
    r = CommandRegistry()
    result = r.parse_command("what time is it")
    assert result["matched"] is True
    assert result["category"] is not None


def test_parse_lights_on():
    r = CommandRegistry()
    result = r.parse_command("turn on the lights")
    assert result["matched"] is True
    assert result["category"] == "smart_home"


def test_parse_empty():
    r = CommandRegistry()
    result = r.parse_command("")
    assert result["matched"] is False


def test_command_list_not_empty():
    r = CommandRegistry()
    assert len(r.commands) > 0


def test_get_categories():
    r = CommandRegistry()
    cats = r.get_categories()
    assert len(cats) > 0
    assert "system" in cats
    assert "smart_home" in cats


def test_get_all_commands():
    r = CommandRegistry()
    cmds = r.get_all_commands()
    assert len(cmds) > 0
    assert all("handler" in c for c in cmds)


def test_parse_run_diagnostics():
    r = CommandRegistry()
    result = r.parse_command("run diagnostics")
    assert result["matched"] is True
    assert result["handler"] == "run_diagnostics"
    assert result["category"] == "system"


def test_parse_start_thermal_logger():
    r = CommandRegistry()
    result = r.parse_command("start the thermal logger")
    assert result["matched"] is True
    assert result["handler"] == "run_diagnostics"


def test_parse_run_diagnostics_not_open_app():
    r = CommandRegistry()
    result = r.parse_command("run diagnostics")
    assert result["handler"] != "open_app"
