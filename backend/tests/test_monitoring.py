import base64
from types import SimpleNamespace

import pytest

from app.services.monitoring_service import MonitoringService
from app.routers.websocket import _monitoring_alert_callback, _broadcast_voice_alert


class FakeProc:
    def __init__(self, name, rss):
        self.info = {"name": name, "memory_info": SimpleNamespace(rss=rss)}


@pytest.fixture
def svc():
    s = MonitoringService()
    s._gpu_info = lambda: {}
    return s


def test_collect_once_includes_process_metrics(svc, monkeypatch):
    monkeypatch.setattr(
        "app.services.monitoring_service.psutil.process_iter",
        lambda attrs=None: iter([
            FakeProc("a.exe", 1 * 1024 * 1024),
            FakeProc("b.exe", 3 * 1024 * 1024),
            FakeProc("c.exe", 2 * 1024 * 1024),
        ]),
    )
    snapshot = svc._collect_once()
    assert snapshot["process_count"] == 3
    assert snapshot["top_process_name"] == "b.exe"
    assert snapshot["top_process_memory_mb"] == 3


def test_process_scan_cached_15s(svc, monkeypatch):
    calls = []

    def fake_iter(attrs=None):
        calls.append(1)
        return iter([FakeProc("a.exe", 1 * 1024 * 1024)])

    monkeypatch.setattr("app.services.monitoring_service.psutil.process_iter", fake_iter)
    svc._collect_once()
    svc._collect_once()
    assert len(calls) == 1


def test_process_count_threshold_alert(svc):
    alerts = svc._check_thresholds({"process_count": 380})
    assert [a["metric"] for a in alerts] == ["process_count"]
    assert alerts[0]["label"] == "Running Processes"
    assert alerts[0]["message"] == "Running Processes at 380 (threshold: 350)"


def test_top_process_memory_threshold_alert(svc):
    alerts = svc._check_thresholds({"top_process_memory_mb": 2500})
    assert [a["metric"] for a in alerts] == ["top_process_memory_mb"]
    assert alerts[0]["label"] == "Largest Process"
    assert alerts[0]["message"] == "Largest Process at 2500 MB (threshold: 2048 MB)"


def test_process_alerts_respect_cooldown(svc):
    snapshot = {"process_count": 380}
    assert svc._check_thresholds(snapshot)
    assert svc._check_thresholds(snapshot) == []


def test_percent_alert_message_unchanged(svc):
    alerts = svc._check_thresholds({"ram_percent": 90.0})
    assert alerts[0]["message"] == "RAM Usage at 90% (threshold: 85%)"


@pytest.mark.anyio
async def test_monitoring_alert_callback_broadcasts_system_alert(monkeypatch):
    sent = []

    async def fake_broadcast(msg):
        sent.append(msg)

    async def fake_tts(text, voice=None, rate=0, pitch=0):
        return b"AUDIO"

    monkeypatch.setattr("app.routers.websocket.broadcast", fake_broadcast)
    monkeypatch.setattr("app.services.voice_service.voice_service.text_to_speech", fake_tts)
    await _monitoring_alert_callback({"metric": "ram_percent", "message": "RAM Usage at 90%"})
    assert sent[0]["type"] == "system_alert"
    assert sent[0]["alert"]["metric"] == "ram_percent"


@pytest.mark.anyio
async def test_broadcast_voice_alert_sends_base64_audio(monkeypatch):
    sent = []

    async def fake_broadcast(msg):
        sent.append(msg)

    async def fake_tts(text, voice=None, rate=0, pitch=0):
        assert "RAM Usage at 90%" in text
        return b"AUDIO"

    monkeypatch.setattr("app.routers.websocket.broadcast", fake_broadcast)
    monkeypatch.setattr("app.services.voice_service.voice_service.text_to_speech", fake_tts)
    await _broadcast_voice_alert({"message": "RAM Usage at 90%"})
    assert sent[-1]["type"] == "voice_alert"
    assert sent[-1]["audio"] == base64.b64encode(b"AUDIO").decode("ascii")


@pytest.mark.anyio
async def test_broadcast_voice_alert_silent_on_tts_error(monkeypatch):
    sent = []

    async def fake_broadcast(msg):
        sent.append(msg)

    async def fake_tts(text, voice=None, rate=0, pitch=0):
        raise RuntimeError("no network")

    monkeypatch.setattr("app.routers.websocket.broadcast", fake_broadcast)
    monkeypatch.setattr("app.services.voice_service.voice_service.text_to_speech", fake_tts)
    await _broadcast_voice_alert({"message": "RAM Usage at 90%"})
    assert all(m["type"] != "voice_alert" for m in sent)
