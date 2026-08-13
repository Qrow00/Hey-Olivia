"""RED/GREEN tests for JARVIS V3 learner (feedback + retrain job)."""
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


def test_pipeline_persists_teaches():
    """Taught examples survive a restart via the model file."""
    from app.nlu.pipeline import NLUPipeline

    model = os.path.join(_tmp(), "clf.json")
    nlu = NLUPipeline(model_path=model)
    assert asyncio.run(nlu.teach("power down the rig", "system_shutdown")) is True
    assert os.path.exists(model)

    nlu2 = NLUPipeline(model_path=model)
    intent, conf = nlu2.classifier.predict("power down the rig")
    assert intent == "system_shutdown"
    assert conf > 0.0


def test_mistake_learner_corrects_previous():
    """'no, I meant X' after a wrong reply re-teaches the last command."""
    from app.learner.feedback import FeedbackStore
    from app.learner.auto_learn import MistakeLearner
    from app.nlu.pipeline import NLUPipeline

    nlu = NLUPipeline()
    fb = FeedbackStore(os.path.join(_tmp(), "fb.db"))
    learner = MistakeLearner(fb, nlu, None)

    async def run():
        await learner.note("what time is it",
                           {"intent": "chat", "confidence": 0.5,
                            "command_type": "chat", "source": "chat"})
        await learner.note("no, I meant what time is it",
                           {"intent": "chat", "confidence": 0.5,
                            "command_type": "chat", "source": "chat"})
        return await fb.training_examples()

    examples = asyncio.run(run())
    assert any(e["text"] == "what time is it" and e["intent"] == "info_time"
               for e in examples)


def test_mistake_learner_records_skill_failure():
    from app.learner.feedback import FeedbackStore
    from app.learner.auto_learn import MistakeLearner
    from app.nlu.pipeline import NLUPipeline

    nlu = NLUPipeline()
    fb = FeedbackStore(os.path.join(_tmp(), "fb.db"))
    learner = MistakeLearner(fb, nlu, None)

    async def run():
        await learner.note("turn on the lights",
                           {"intent": "smart_home_turn_on", "confidence": 0.9,
                            "command_type": "skill", "source": "regex",
                            "success": False})
        return await fb.stats()

    stats = asyncio.run(run())
    assert stats["bad"] == 1


def test_mistake_learner_first_message_no_crash():
    from app.learner.feedback import FeedbackStore
    from app.learner.auto_learn import MistakeLearner
    from app.nlu.pipeline import NLUPipeline

    learner = MistakeLearner(FeedbackStore(os.path.join(_tmp(), "fb.db")),
                             NLUPipeline(), None)

    async def run():
        await learner.note("no, i meant something else",
                           {"intent": "chat", "confidence": 0.5,
                            "command_type": "chat", "source": "chat"})
        return True

    assert asyncio.run(run()) is True
