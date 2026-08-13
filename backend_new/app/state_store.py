"""StateStore - Centralized per-profile state management.

Stores:
- Per-profile: personality, settings, conversation memory, voice profile
- Observable: services subscribe to change notifications
- SQLite-backed with JSON cache for speed
- Change broadcasting to subscribed services
"""

import json
import sqlite3
import asyncio
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path


class StateStore:
    """Centralized, partitioned state store with per-profile scoping."""
    
    def __init__(self, db_path: str = "jarvis.db", data_dir: str = "data"):
        self.db_path = db_path
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize SQLite
        self._init_db()
        
        # State: {profile_name: {key: value}}
        self._state: Dict[str, Dict[str, Any]] = {}
        
        # Change subscribers: {profile_name: [callback]}
        self._subscribers: Dict[str, List[Callable]] = {}
        
        # Load existing data
        self._reload_state()
    
    def _init_db(self) -> None:
        """Initialize SQLite database tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS state_store (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            profile TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )''')
        conn.commit()
        conn.close()
    
    def _reload_state(self) -> None:
        """Load state from SQLite, reconciling with JSON files."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT key, value, profile FROM state_store")
        rows = c.fetchall()
        conn.close()
        
        for key, value, profile in rows:
            try:
                val = json.loads(value)
                if profile not in self._state:
                    self._state[profile] = {}
                self._state[profile][key] = val
            except (json.JSONDecodeError, TypeError):
                continue
    
    def set(self, profile: str, key: str, value: Any) -> None:
        """Set a state value for a profile, write to SQLite + JSON, notify subscribers."""
        import datetime
        
        if profile not in self._state:
            self._state[profile] = {}
        self._state[profile][key] = value
        
        # Write to SQLite
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO state_store (key, value, profile, updated_at) VALUES (?, ?, ?, ?)",
            (key, json.dumps(value), profile, datetime.datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        
        # Write to JSON data file
        data_file = self.data_dir / f"{profile}.json"
        profile_data = self._state[profile]
        with open(data_file, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        # Notify subscribers
        self._notify(profile, {"type": "state_change", "key": key, "value": value})
    
    def get(self, profile: str, key: str, default: Any = None) -> Any:
        """Get a state value for a profile."""
        if profile in self._state and key in self._state[profile]:
            return self._state[profile][key]
        return default
    
    def subscribe(self, profile: str, callback: Callable) -> None:
        """Subscribe to state change notifications for a profile."""
        if profile not in self._subscribers:
            self._subscribers[profile] = []
        self._subscribers[profile].append(callback)
    
    def _notify(self, profile: str, message: Dict[str, Any]) -> None:
        """Notify all subscribers for a profile."""
        for callback in self._subscribers.get(profile, []):
            try:
                callback(message)
            except Exception as e:
                print(f"Error in state subscriber: {e}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all subscribers across all profiles."""
        for profile, callbacks in self._subscribers.items():
            for callback in callbacks:
                try:
                    result = callback(message)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    print(f"Error in state subscriber for {profile}: {e}")
    
    def get_active_profile(self) -> Optional[str]:
        """Get the currently active profile name."""
        # Look for a profile marked as active, or return the first one
        for profile in self._state:
            # Check if profile has an 'active' marker in JSON
            data_file = self.data_dir / f"{profile}.json"
            if data_file.exists():
                try:
                    with open(data_file) as f:
                        data = json.load(f)
                    if data.get("active") == profile:
                        return profile
                except (json.JSONDecodeError, TypeError):
                    pass
            return profile  # Return first available
        return None
    
    def switch_profile(self, new_profile: str) -> None:
        """Switch to a new profile, persisting current state."""
        # Save current profile's data to JSON
        active = self.get_active_profile()
        if active and active in self._state:
            data_file = self.data_dir / f"{active}.json"
            with open(data_file, 'w') as f:
                json.dump(self._state[active], f, indent=2)
        
        # Set new profile as active
        if new_profile not in self._state:
            self._state[new_profile] = {}
        
        # Write JSON for new profile
        data_file = self.data_dir / f"{new_profile}.json"
        with open(data_file, 'w') as f:
            json.dump(self._state[new_profile], f, indent=2)