"""RED/GREEN tests for JARVIS V3 intent classifier (pure-python, trainable)."""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _build_classifier():
    from app.nlu.intent_classifier import IntentClassifier
    from app.nlu.training_data import SEED_INTENTS

    clf = IntentClassifier()
    clf.train(SEED_INTENTS)
    return clf


def test_train_and_predict_known_intent():
    clf = _build_classifier()
    intent, score = clf.predict("what time is it right now")
    assert intent == "info_time"
    assert score > 0.2


def test_predict_email_intent():
    clf = _build_classifier()
    intent, _ = clf.predict("read my inbox and tell me what is new")
    assert intent == "email_read"


def test_predict_chat_fallback():
    clf = _build_classifier()
    intent, _ = clf.predict("tell me a story about a dragon")
    assert intent == "chat"


def test_add_example_incremental():
    from app.nlu.intent_classifier import IntentClassifier
    clf = IntentClassifier()
    clf.add_example("start the reactor", "power_reactor")
    clf.add_example("begin the reactor now", "power_reactor")
    intent, _ = clf.predict("start the reactor please")
    assert intent == "power_reactor"


def test_save_and_load(tmp_path=None):
    import tempfile as tf
    from app.nlu.intent_classifier import IntentClassifier
    clf = _build_classifier()
    path = os.path.join(tf.mkdtemp(), "clf.json")
    clf.save(path)
    clf2 = IntentClassifier()
    clf2.load(path)
    intent, _ = clf2.predict("what time is it")
    assert intent == "info_time"


def test_empty_predict_returns_chat():
    from app.nlu.intent_classifier import IntentClassifier
    clf = IntentClassifier()
    intent, score = clf.predict("anything at all")
    assert intent == "chat"
    assert score == 0.0
