"""RED/GREEN tests for JARVIS V4 fast-path patterns."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_time():
    from app.nlu.patterns import match_fast
    r = match_fast("what time is it")
    assert r is not None
    assert r["intent"] == "info_time"


def test_shutdown():
    from app.nlu.patterns import match_fast
    r = match_fast("shutdown the computer")
    assert r is not None
    assert r["intent"] == "system_shutdown"


def test_turn_on_light_entity():
    from app.nlu.patterns import match_fast
    r = match_fast("turn on the kitchen lights")
    assert r is not None
    assert r["intent"] == "smart_home_turn_on"
    assert "kitchen lights" in r["params"]["device"]


def test_thermostat_entity():
    from app.nlu.patterns import match_fast
    r = match_fast("set the thermostat to 72")
    assert r is not None
    assert r["intent"] == "smart_home_set_thermostat"
    assert r["params"]["temperature"] == "72"


def test_browser_navigate():
    from app.nlu.patterns import match_fast
    r = match_fast("open youtube.com")
    assert r is not None
    assert r["intent"] == "browser_navigate"


def test_email_read():
    from app.nlu.patterns import match_fast
    r = match_fast("check my email")
    assert r is not None
    assert r["intent"] == "email_read"


def test_camera_capture():
    from app.nlu.patterns import match_fast
    r = match_fast("take a picture")
    assert r is not None
    assert r["intent"] == "camera_capture"


def test_personality_slider():
    from app.nlu.patterns import match_fast
    r = match_fast("be more sarcastic")
    assert r is not None
    assert r["intent"] == "set_personality"
    assert r["params"]["trait"] == "sarcastic"


def test_no_match_returns_none():
    from app.nlu.patterns import match_fast
    r = match_fast("tell me about the history of quantum computing")
    assert r is None
