import asyncio

import pytest

from app.services.diagnostics_service import DiagnosticsService

ALL_CHECKS = [
    "CPU", "RAM", "Disk", "GPU", "Battery", "LLM (Ollama)",
    "Speech-to-text (Whisper)", "Text-to-speech (edge-tts)", "Wake word",
    "Internet", "Tailscale", "Browser", "Cameras", "Smart home", "Thermal logger",
]


@pytest.fixture
def svc():
    return DiagnosticsService()


@pytest.mark.anyio
async def test_run_returns_full_report(svc):
    async def fake(name):
        return {"name": name, "status": "ok", "detail": "ok"}

    svc._all_checks = lambda: [(n, fake(n)) for n in ALL_CHECKS]
    report = await svc.run()
    assert report["status"] == "success"
    assert len(report["checks"]) == 15
    assert report["summary"] == "15 of 15 checks passed"
    assert report["failed"] == []
    assert all(c["status"] in ("ok", "warn", "fail", "skip") for c in report["checks"])


@pytest.mark.anyio
async def test_run_isolates_failures(svc):
    async def ok_check(name):
        return {"name": name, "status": "ok", "detail": "ok"}

    async def bad_check():
        raise RuntimeError("boom")

    svc._all_checks = lambda: [("A", ok_check("A")), ("B", bad_check())]
    report = await svc.run()
    assert report["summary"] == "1 of 2 checks passed"
    assert report["failed"] == ["B"]
    statuses = {c["name"]: c["status"] for c in report["checks"]}
    assert statuses["A"] == "ok"
    assert statuses["B"] == "fail"


@pytest.mark.anyio
async def test_run_times_out_slow_check(svc):
    svc._check_timeout = 0.1

    async def slow():
        await asyncio.sleep(2)
        return {"name": "slow", "status": "ok", "detail": "ok"}

    svc._all_checks = lambda: [("slow", slow())]
    report = await svc.run()
    assert report["summary"] == "0 of 1 checks passed"
    assert report["checks"][0]["status"] == "fail"
    assert report["checks"][0]["detail"] == "timed out"
