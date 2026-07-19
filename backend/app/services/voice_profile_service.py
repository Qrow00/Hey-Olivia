from dataclasses import dataclass, field, asdict
from typing import Optional
import json
from pathlib import Path


@dataclass
class VoiceProfile:
    id: str
    name: str
    voice: str
    rate: int = 0
    pitch: int = 0
    volume: float = 1.0
    description: str = ""
    language: str = "en-US"
    is_default: bool = False


class VoiceProfileService:
    def __init__(self, data_dir: str = "data/voices"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.profiles: dict[str, VoiceProfile] = {}
        self.active_profile_id: str = "jarvis"
        self._load()

    def _load(self):
        profiles_file = self.data_dir / "profiles.json"
        if profiles_file.exists():
            data = json.loads(profiles_file.read_text())
            self.active_profile_id = data.get("active_profile", "jarvis")
            for p in data.get("profiles", []):
                profile = VoiceProfile(**p)
                self.profiles[profile.id] = profile

        if not self.profiles:
            self._create_defaults()

    def _create_defaults(self):
        defaults = [
            VoiceProfile(
                id="jarvis",
                name="J.A.R.V.I.S.",
                voice="en-US-GuyNeural",
                rate=0,
                pitch=0,
                description="British butler, calm and precise",
                is_default=True,
            ),
            VoiceProfile(
                id="friday",
                name="Friday",
                voice="en-US-JennyNeural",
                rate=5,
                pitch=2,
                description="Friendly and efficient",
            ),
            VoiceProfile(
                id="edith",
                name="Edith",
                voice="en-US-AriaNeural",
                rate=-5,
                pitch=-1,
                description="Warm and measured",
            ),
            VoiceProfile(
                id="tobby",
                name="Tobby",
                voice="en-US-ChristopherNeural",
                rate=10,
                pitch=3,
                description="Energetic and upbeat",
            ),
            VoiceProfile(
                id="karen",
                name="Karen",
                voice="en-US-SaraNeural",
                rate=0,
                pitch=1,
                description="Professional and clear",
            ),
        ]
        for p in defaults:
            self.profiles[p.id] = p
        self._save()

    def _save(self):
        profiles_file = self.data_dir / "profiles.json"
        profiles_file.write_text(json.dumps({
            "active_profile": self.active_profile_id,
            "profiles": [asdict(p) for p in self.profiles.values()],
        }, indent=2))

    def get_active_profile(self) -> VoiceProfile:
        return self.profiles.get(self.active_profile_id, self.profiles["jarvis"])

    def set_active(self, profile_id: str) -> dict:
        if profile_id not in self.profiles:
            return {"status": "error", "message": f"Profile '{profile_id}' not found"}
        self.active_profile_id = profile_id
        self._save()
        profile = self.profiles[profile_id]
        return {"status": "activated", "profile": asdict(profile)}

    def create_profile(self, profile_id: str, name: str, voice: str,
                       rate: int = 0, pitch: int = 0, description: str = "") -> dict:
        if profile_id in self.profiles:
            return {"status": "error", "message": f"Profile '{profile_id}' already exists"}
        profile = VoiceProfile(
            id=profile_id, name=name, voice=voice,
            rate=rate, pitch=pitch, description=description,
        )
        self.profiles[profile_id] = profile
        self._save()
        return {"status": "created", "profile": asdict(profile)}

    def update_profile(self, profile_id: str, **kwargs) -> dict:
        if profile_id not in self.profiles:
            return {"status": "error", "message": f"Profile '{profile_id}' not found"}
        profile = self.profiles[profile_id]
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        self._save()
        return {"status": "updated", "profile": asdict(profile)}

    def delete_profile(self, profile_id: str) -> dict:
        if profile_id not in self.profiles:
            return {"status": "error", "message": f"Profile '{profile_id}' not found"}
        if self.profiles[profile_id].is_default:
            return {"status": "error", "message": "Cannot delete default profile"}
        if profile_id == self.active_profile_id:
            self.active_profile_id = "jarvis"
        del self.profiles[profile_id]
        self._save()
        return {"status": "deleted"}

    def list_profiles(self) -> list:
        profiles = [asdict(p) for p in self.profiles.values()]
        for p in profiles:
            p["is_active"] = p["id"] == self.active_profile_id
        return profiles

    def get_edge_tts_config(self, profile_id: str = None) -> dict:
        profile = self.profiles.get(profile_id or self.active_profile_id, self.get_active_profile())
        return {
            "voice": profile.voice,
            "rate": f"+{profile.rate}%" if profile.rate >= 0 else f"{profile.rate}%",
            "pitch": f"+{profile.pitch}Hz" if profile.pitch >= 0 else f"{profile.pitch}Hz",
            "volume": f"+{profile.volume * 100 - 100:.0f}%",
        }


voice_profile_service = VoiceProfileService()
