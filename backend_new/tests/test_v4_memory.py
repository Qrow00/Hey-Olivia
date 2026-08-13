"""RED/GREEN tests for JARVIS V4 memory (profile, vector store, episodic)."""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _tmpdir():
    return tempfile.mkdtemp()


def test_profile_preferences():
    from app.state_store import StateStore
    from app.memory.profile import ProfileStore

    store = StateStore(db_path=os.path.join(_tmpdir(), "s.db"), data_dir=_tmpdir())
    p = ProfileStore(store, "default")
    p.set_pref("favorite_song", "Iron Man")
    assert p.get_pref("favorite_song") == "Iron Man"
    assert p.get_pref("nope", "x") == "x"


def test_vector_store_add_and_search():
    from app.memory.vector_store import VectorStore

    vs = VectorStore(os.path.join(_tmpdir(), "v.json"))
    vs.add("1", "what time is it", [1.0, 0.0])
    vs.add("2", "turn on lights", [0.0, 1.0])
    results = vs.search([0.8, 0.2], k=1)
    assert results[0][0] == "1"


def test_vector_store_persistence():
    from app.memory.vector_store import VectorStore

    path = os.path.join(_tmpdir(), "v.json")
    vs = VectorStore(path)
    vs.add("1", "hello", [1.0, 0.0])
    vs2 = VectorStore(path)
    vs2.load()
    results = vs2.search([1.0, 0.1], k=1)
    assert results[0][0] == "1"


def test_episodic_memory():
    import asyncio
    from app.memory.episodic import EpisodicMemory

    db = os.path.join(_tmpdir(), "m.db")
    mem = EpisodicMemory(db)
    asyncio.run(mem.add_turn("user", "hello", {"intent": "greeting"}))
    history = asyncio.run(mem.recent(5))
    assert len(history) == 1
    assert history[0]["role"] == "user"


def test_episodic_memory_broadcast():
    import asyncio
    from app.memory.episodic import EpisodicMemory

    db = os.path.join(_tmpdir(), "m.db")
    mem = EpisodicMemory(db)
    received = []
    mem.subscribe(lambda m: received.append(m))
    asyncio.run(mem.add_turn("user", "hi", {}))
    assert any(m["type"] == "memory_turn" for m in received)
