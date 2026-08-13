"""RED/GREEN tests for JARVIS V4 personality (emotional sliders)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_default_sliders():
    from app.chat.personality import Personality
    p = Personality(None, profile="default")
    vals = p.sliders()
    assert vals["humor"] == 0.5
    assert vals["sarcasm"] == 0.3


def test_set_slider_validates_range():
    from app.chat.personality import Personality
    p = Personality(None, profile="default")
    assert p.set_slider("humor", 1.0) is True
    assert p.set_slider("sarcasm", 1.5) is False
    assert p.set_slider("bogus", 0.5) is False
    assert p.sliders()["humor"] == 1.0


def test_system_prompt_reflects_sliders():
    from app.chat.personality import Personality
    p = Personality(None, profile="default")
    prompt = p.system_prompt()
    assert "J.A.R.V.I.S." in prompt
    assert "sarcasm" in prompt.lower()


def test_tts_mapping_changes_with_sliders():
    from app.chat.personality import Personality
    p = Personality(None, profile="default")
    base = p.tts_params()
    p.set_slider("energy", 0.0)
    low = p.tts_params()
    p.set_slider("energy", 1.0)
    high = p.tts_params()
    assert low["rate"] < high["rate"]


def test_warmth_changes_voice():
    from app.chat.personality import Personality
    p = Personality(None, profile="default")
    cold = p.tts_params()
    p.set_slider("warmth", 1.0)
    warm = p.tts_params()
    assert cold["voice"] != warm["voice"]


def test_sliders_persist_through_state_store():
    import tempfile, sqlite3
    from app.state_store import StateStore
    from app.chat.personality import Personality

    db = os.path.join(tempfile.mkdtemp(), "test.db")
    store = StateStore(db_path=db, data_dir=os.path.join(tempfile.mkdtemp(), "data"))
    p = Personality(store, profile="default")
    p.set_slider("sarcasm", 0.9)

    p2 = Personality(store, profile="default")
    assert p2.sliders()["sarcasm"] == 0.9
