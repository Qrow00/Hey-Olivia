"""RED/GREEN tests for JARVIS V4 entity extraction."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_extract_numbers():
    from app.nlu.entity_extractor import extract_entities
    r = extract_entities("set the thermostat to 72", "smart_home_set_thermostat")
    assert r.get("temperature") == "72"


def test_extract_time():
    from app.nlu.entity_extractor import extract_entities
    r = extract_entities("set an alarm at 7 30 am", "scheduler_alarm")
    assert "7" in r.get("time", "")


def test_extract_app_target():
    from app.nlu.entity_extractor import extract_entities
    r = extract_entities("open youtube", "browser_navigate")
    assert r.get("target") == "youtube.com"


def test_extract_query():
    from app.nlu.entity_extractor import extract_entities
    r = extract_entities("search youtube for funny cat videos", "browser_youtube")
    assert "cat" in r.get("query", "")


def test_extract_nothing_returns_empty():
    from app.nlu.entity_extractor import extract_entities
    r = extract_entities("hello there", "greeting")
    assert r == {}
