"""RED/GREEN tests for JARVIS V3 API + WebSocket contract."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    os.environ.setdefault("JARVIS_SERVICES", "full")
    os.environ.setdefault("JARVIS_DB_PATH", "test_v4.db")
    from app.api.main import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "skills" in body


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "J.A.R.V.I.S." in r.json()["name"]


def test_skills_endpoint(client):
    r = client.get("/skills")
    assert r.status_code == 200
    assert "enabled" in r.json()


def test_personality_get(client):
    r = client.get("/personality")
    assert r.status_code == 200
    assert "sarcasm" in r.json()


def test_personality_update(client):
    r = client.put("/personality", json={"humor": 0.8})
    assert r.status_code == 200
    assert r.json()["humor"] == 0.8
    r = client.get("/personality")
    assert r.json()["humor"] == 0.8


def test_command_endpoint(client):
    r = client.post("/command", json={"text": "what time is it"})
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "info_time"


def test_command_chat_fallback(client):
    r = client.post("/command", json={"text": "tell me a fun story"})
    assert r.status_code == 200
    assert r.json()["intent"] == "chat"
