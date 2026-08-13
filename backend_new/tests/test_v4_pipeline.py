"""RED/GREEN tests for JARVIS V4 NLU pipeline (regex -> classifier -> chat)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_pipeline_instantiation():
    from app.nlu.pipeline import NLUPipeline
    p = NLUPipeline()
    assert p is not None


def test_pipeline_fast_path():
    import asyncio
    from app.nlu.pipeline import NLUPipeline
    p = NLUPipeline()
    result = asyncio.run(p.process("what time is it"))
    assert result["intent"] == "info_time"
    assert result["source"] == "regex"
    assert result["confidence"] > 0.9


def test_pipeline_classifier_path():
    import asyncio
    from app.nlu.pipeline import NLUPipeline
    p = NLUPipeline()
    result = asyncio.run(p.process("read my inbox please"))
    assert result["intent"] == "email_read"
    assert result["source"] in ("regex", "classifier")


def test_pipeline_chat_fallback():
    import asyncio
    from app.nlu.pipeline import NLUPipeline
    p = NLUPipeline()
    result = asyncio.run(p.process("tell me a story about a flying castle"))
    assert result["intent"] == "chat"
    assert result["source"] == "chat"


def test_pipeline_teach_example_captures():
    import asyncio
    from app.nlu.pipeline import NLUPipeline
    p = NLUPipeline()
    result = asyncio.run(p.process("teach me something interesting"))
    # Unrecognized, should route to chat rather than crash
    assert result["intent"] == "chat"
