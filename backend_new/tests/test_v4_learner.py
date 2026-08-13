"""RED/GREEN tests for JARVIS V4 learner (feedback + retrain job)."""
import sys
import os
import asyncio
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _tmp():
    return tempfile.mkdtemp()


def test_feedback_store_record_and_count():
    from app.learner.feedback import FeedbackStore

    db = os.path.join(_tmp(), "fb.db")
    fb = FeedbackStore(db)
    asyncio.run(fb.record("what time is it", "info_time", "good", "Great."))
    asyncio.run(fb.record("tell me a joke", "chat", "bad", "Not funny."))
    stats = asyncio.run(fb.stats())
    assert stats["total"] == 2
    assert stats["good"] == 1


def test_feedback_can_teach_example():
    """User can mark a phrasing that should map to an intent -> new training example."""
    import json
    from app.learner.feedback import FeedbackStore

    db = os.path.join(_tmp(), "fb.db")
    fb = FeedbackStore(db)
    asyncio.run(fb.record("power down the rig", "system_shutdown", "bad", "This should shut down"))
    examples = asyncio.run(fb.training_examples())
    assert any(e["text"] == "power down the rig" for e in examples)


def test_retrain_job_creates_classifier():
    from app.learner.retrain_job import retrain_from_feedback

    db = os.path.join(_tmp(), "fb.db")
    fb_store = None
    from app.learner.feedback import FeedbackStore
    fb_store = FeedbackStore(db)
    asyncio.run(fb_store.record("kill the power", "system_shutdown", "good", "ok"))
    asyncio.run(fb_store.record("shut it down", "system_shutdown", "good", "ok"))
    asyncio.run(fb_store.record("what is the time", "info_time", "good", "ok"))
    model_path = os.path.join(_tmp(), "clf.json")
    result = asyncio.run(retrain_from_feedback(fb_store, model_path))
    assert result is True
    assert os.path.exists(model_path)
