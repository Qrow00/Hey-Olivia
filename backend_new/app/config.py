"""Central configuration for J.A.R.V.I.S. V3 (Agent Core).

All settings are overridable via environment variables. Heavy optional
dependencies are never imported here so the core always runs.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # backend_new/
APP_DIR = Path(__file__).resolve().parent          # backend_new/app/

PERSONALITY_SLIDERS = ["humor", "sarcasm", "warmth", "energy", "formality", "curiosity"]

DEFAULT_PERSONALITY = {
    "humor": 0.5,
    "sarcasm": 0.3,
    "warmth": 0.6,
    "energy": 0.5,
    "formality": 0.4,
    "curiosity": 0.6,
}


def _env(name: str, default):
    val = os.environ.get(name)
    if val is None:
        return default
    if isinstance(default, bool):
        return val.lower() in ("1", "true", "yes", "on")
    if isinstance(default, int):
        return int(val)
    if isinstance(default, float):
        return float(val)
    return val


class Config:
    """Runtime configuration, loaded once at startup."""

    def __init__(self):
        self.host = _env("JARVIS_HOST", "0.0.0.0")
        self.port = _env("JARVIS_PORT", 8000)
        self.db_path = _env("JARVIS_DB_PATH", str(BASE_DIR / "jarvis_v3.db"))
        self.data_dir = Path(_env("JARVIS_DATA_DIR", str(BASE_DIR / "data")))
        self.models_dir = Path(_env("JARVIS_MODELS_DIR", str(BASE_DIR / "models")))

        # Services gating (same semantics as V3 JARVIS_SERVICES)
        self.services = _env("JARVIS_SERVICES", "full")

        # Chat model: prefer an OpenAI-compatible llama-server endpoint,
        # otherwise fall back to in-process GGUF, otherwise template replies.
        self.chat_api_base = _env("JARVIS_CHAT_API", "http://127.0.0.1:8080/v1")
        self.chat_api_key = _env("JARVIS_CHAT_API_KEY", "local")
        self.chat_model_name = _env("JARVIS_CHAT_MODEL", "local")
        self.chat_gguf_path = _env(
            "JARVIS_CHAT_GGUF",
            str(self.models_dir / "Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        )
        self.chat_use_llama_server = _env("JARVIS_USE_LLAMA_SERVER", False)
        self.chat_temperature = _env("JARVIS_CHAT_TEMPERATURE", 0.7)
        self.chat_max_tokens = _env("JARVIS_CHAT_MAX_TOKENS", 512)

        # Voice
        self.wake_word_model = _env(
            "JARVIS_WAKE_WORD_MODEL", str(self.models_dir / "jarvis_wakeword.onnx")
        )
        self.wake_word_phrases = ["jarvis", "hey jarvis"]
        self.stt_model_size = _env("JARVIS_STT_MODEL", "small")
        self.vad_threshold = _env("JARVIS_VAD_THRESHOLD", 0.5)
        self.tts_voice_default = _env("JARVIS_TTS_VOICE", "en-GB-RyanNeural")
        self.tts_provider = _env("JARVIS_TTS_PROVIDER", "piper")
        self.tts_piper_model = _env(
            "JARVIS_TTS_PIPER_MODEL", str(self.models_dir / "piper" / "en_GB-alan-medium.onnx")
        )
        self.tts_kokoro_voice = _env("JARVIS_TTS_KOKORO_VOICE", "bm_george")
        self.tts_kokoro_model = _env(
            "JARVIS_TTS_KOKORO_MODEL", str(self.models_dir / "kokoro" / "kokoro-v1.0.onnx")
        )
        self.tts_kokoro_voices = _env(
            "JARVIS_TTS_KOKORO_VOICES", str(self.models_dir / "kokoro" / "voices-v1.0.bin")
        )

        # Vision
        self.yunet_model = _env("JARVIS_YUNET_MODEL", str(self.models_dir / "yunet.onnx"))
        self.face_embed_model = _env(
            "JARVIS_FACE_EMBED_MODEL", str(self.models_dir / "mobilefacenet.onnx")
        )
        self.face_match_threshold = _env("JARVIS_FACE_MATCH_THRESHOLD", 0.55)

        # Memory / learner
        self.conv_history_size = _env("JARVIS_CONV_HISTORY", 8)
        self.retrain_interval_s = _env("JARVIS_RETRAIN_INTERVAL", 300)
        self.retrain_min_samples = _env("JARVIS_RETRAIN_MIN_SAMPLES", 5)

        self.profile = _env("JARVIS_PROFILE", "default")

        # Access token: when set, REST (except / and /health) and WebSocket
        # require it. Empty = open (local dev). Set JARVIS_TOKEN before
        # exposing the server beyond localhost.
        self.access_token = _env("JARVIS_TOKEN", "")

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)

    def service_enabled(self, service: str) -> bool:
        """True if a service group is enabled by JARVIS_SERVICES."""
        parts = self.services.strip().lower().split()
        if not parts or parts[0] == "full":
            return True
        return service in parts


config = Config()
