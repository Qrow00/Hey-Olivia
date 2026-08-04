import json
import uuid
from pathlib import Path
from threading import Lock
from datetime import datetime, timezone

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PROFILES_FILE = DATA_DIR / "profiles.json"

DEFAULT_PROFILES = {
    "profiles": [
        {
            "id": "default",
            "name": "Default",
            "avatar": "",
            "is_admin": True,
            "created_at": "",
        }
    ]
}


class AuthService:
    def __init__(self):
        self._sessions: dict[str, str] = {}
        self._lock = Lock()
        self._profiles: list[dict] = []
        self._load()

    def _ensure_file(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self):
        self._ensure_file()
        if PROFILES_FILE.exists():
            try:
                with open(PROFILES_FILE) as f:
                    data = json.load(f)
                self._profiles = data.get("profiles", [])
            except (json.JSONDecodeError, OSError):
                self._profiles = list(DEFAULT_PROFILES["profiles"])
        else:
            self._profiles = list(DEFAULT_PROFILES["profiles"])
            self._save()

        for p in self._profiles:
            if not p.get("created_at"):
                p["created_at"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def _save(self):
        self._ensure_file()
        with open(PROFILES_FILE, "w") as f:
            json.dump({"profiles": self._profiles}, f, indent=2)

    def list_profiles(self) -> list[dict]:
        with self._lock:
            return [
                {"id": p["id"], "name": p["name"], "avatar": p.get("avatar", "")}
                for p in self._profiles
            ]

    def create_session(self, profile_id: str) -> dict | None:
        with self._lock:
            profile = next((p for p in self._profiles if p["id"] == profile_id), None)
            if not profile:
                return None
            token = str(uuid.uuid4())
            self._sessions[token] = profile_id
            return {
                "token": token,
                "profile": {
                    "id": profile["id"],
                    "name": profile["name"],
                    "avatar": profile.get("avatar", ""),
                    "is_admin": profile.get("is_admin", False),
                },
            }

    def resolve_token(self, token: str) -> str | None:
        return self._sessions.get(token)

    def revoke_session(self, token: str):
        with self._lock:
            self._sessions.pop(token, None)

    def get_profile(self, profile_id: str) -> dict | None:
        with self._lock:
            profile = next((p for p in self._profiles if p["id"] == profile_id), None)
            return dict(profile) if profile else None

    def update_profile(self, profile_id: str, updates: dict):
        with self._lock:
            for p in self._profiles:
                if p["id"] == profile_id:
                    p.update(updates)
                    self._save()
                    return dict(p)
            return None

    def create_profile(self, profile_id: str, name: str, avatar: str = "") -> dict:
        with self._lock:
            profile = {
                "id": profile_id,
                "name": name,
                "avatar": avatar,
                "is_admin": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._profiles.append(profile)
            self._save()
            return profile


auth_service = AuthService()
