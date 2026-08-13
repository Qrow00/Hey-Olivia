"""RED/GREEN tests for JARVIS V3 vision (face db, recognizer graceful degrade)."""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_face_db_add_and_match():
    from app.config import Config
    from app.vision.face_db import FaceDB

    cfg = Config()
    cfg.data_dir = tempfile.mkdtemp()
    cfg.db_path = os.path.join(tempfile.mkdtemp(), "faces.db")
    db = FaceDB(cfg)
    db.add("Tony", [0.1, 0.2, 0.3])
    name, score = db.match([0.1, 0.2, 0.31])
    assert name == "Tony"
    assert score > 0.9


def test_face_db_no_match_returns_unknown():
    from app.config import Config
    from app.vision.face_db import FaceDB

    cfg = Config()
    cfg.data_dir = tempfile.mkdtemp()
    cfg.db_path = os.path.join(tempfile.mkdtemp(), "faces.db")
    db = FaceDB(cfg)
    db.add("Tony", [0.1, 0.2, 0.3])
    # [0.9,0.8,0.7] is cosine-similar to Tony (same octant); use a truly
    # different direction so the match must fail against the threshold.
    name, score = db.match([-0.9, -0.8, -0.7])
    assert name == "unknown"
    assert score < 0.5


def test_face_recognizer_degrades_gracefully():
    """Without opencv/onnxruntime models, recognize() must not crash."""
    import asyncio
    from app.config import Config
    from app.vision.face_recognize import FaceRecognizer

    cfg = Config()
    cfg.models_dir = tempfile.mkdtemp()  # no models here
    rec = FaceRecognizer(cfg)
    result = asyncio.run(rec.recognize(None))
    assert result["success"] is False
    assert "available" in result["narration"]
