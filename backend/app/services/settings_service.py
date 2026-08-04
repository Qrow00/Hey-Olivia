import json
from pathlib import Path
from threading import Lock

DATA_DIR = Path(__file__).parent.parent.parent / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "voice": {
        "wake_word_enabled": True,
        "wake_word_sensitivity": 0.5,
        "tts_voice": "en-US-GuyNeural",
        "voice_profile": "jarvis",
        "llm_model": "llama3.2",
        "stt_model": "tiny",
        "push_to_talk": False,
    },
    "ui": {
        "dark_mode": True,
        "notifications_enabled": True,
    },
    "health": {
        "alerts_enabled": False,
        "heart_rate_alerts": True,
        "spo2_alerts": True,
    },
    "smart_home": {
        "mqtt_broker": "",
        "mqtt_port": 1883,
        "mqtt_username": "",
        "mqtt_password": "",
    },
}


class SettingsService:
    def __init__(self):
        self._profiles: dict[str, dict] = {}
        self._lock = Lock()
        self._load()

    def _ensure_file(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self):
        self._ensure_file()
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE) as f:
                    self._profiles = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._profiles = {}
        if "default" not in self._profiles:
            self._profiles["default"] = {}
            self._save()

    def _save(self):
        self._ensure_file()
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._profiles, f, indent=2)

    def _deep_merge(self, base: dict, override: dict) -> dict:
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def get_all(self, profile_id: str = "default") -> dict:
        with self._lock:
            overrides = self._profiles.get(profile_id, {})
            return self._deep_merge(DEFAULT_SETTINGS, overrides)

    def get(self, profile_id: str, category: str, key: str = None):
        full = self.get_all(profile_id)
        section = full.get(category)
        if section is None:
            return None
        if key is None:
            return dict(section)
        return section.get(key)

    def update(self, profile_id: str, partial: dict) -> dict:
        with self._lock:
            current = self._profiles.get(profile_id, {})
            merged = self._deep_merge(current, partial)
            self._profiles[profile_id] = merged
            self._save()
            return self._deep_merge(DEFAULT_SETTINGS, merged)

    def reset(self, profile_id: str) -> dict:
        with self._lock:
            self._profiles.pop(profile_id, None)
            self._save()
            return dict(DEFAULT_SETTINGS)


settings_service = SettingsService()
