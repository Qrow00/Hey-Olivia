"""ProfileStore - per-user preferences and long-term facts via StateStore."""

from typing import Any, Dict, Optional


class ProfileStore:
    """Read/write persistent user profile data (preferences, facts)."""

    def __init__(self, state_store=None, profile: str = "default"):
        self._store = state_store
        self._profile = profile

    def set_pref(self, key: str, value: Any) -> None:
        if self._store is not None:
            self._store.set(self._profile, f"prefs.{key}", value)

    def get_pref(self, key: str, default: Any = None) -> Any:
        if self._store is not None:
            return self._store.get(self._profile, f"prefs.{key}", default)
        return default

    def remember(self, key: str, value: Any) -> None:
        """Long-term episodic fact about the user/context."""
        if self._store is not None:
            self._store.set(self._profile, f"facts.{key}", value)

    def recall(self, key: str, default: Any = None) -> Any:
        if self._store is not None:
            return self._store.get(self._profile, f"facts.{key}", default)
        return default

    def all_prefs(self) -> Dict[str, Any]:
        if self._store is None:
            return {}
        return dict(self._store.get(self._profile, "prefs", {}) or {})

    def profile_name(self) -> str:
        return self._profile
