"""RED/GREEN tests for JARVIS V3 config."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_config_defaults():
    from app.config import Config
    cfg = Config()
    assert cfg.profile == "default"
    assert cfg.service_enabled("voice") is True
    assert cfg.port == 8000


def test_config_service_gating():
    from app.config import Config
    import os
    os.environ["JARVIS_SERVICES"] = "voice email"
    try:
        cfg = Config()
        assert cfg.service_enabled("voice") is True
        assert cfg.service_enabled("email") is True
        assert cfg.service_enabled("vision") is False
        assert cfg.service_enabled("memory") is False
    finally:
        os.environ.pop("JARVIS_SERVICES", None)


def test_config_full_service_enables_all():
    from app.config import Config
    cfg = Config()
    assert cfg.service_enabled("voice") is True
    assert cfg.service_enabled("vision") is True
    assert cfg.service_enabled("learner") is True


def test_config_ensure_dirs():
    from app.config import Config
    import tempfile
    cfg = Config()
    cfg.ensure_dirs()
    assert cfg.data_dir.exists()
    assert cfg.models_dir.exists()
