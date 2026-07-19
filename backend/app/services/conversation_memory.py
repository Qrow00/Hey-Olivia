import json
import os
import time
from datetime import datetime


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "conversation_memory.json")
MAX_HISTORY = 50
MAX_SESSIONS = 100


class ConversationMemory:
    def __init__(self):
        self._sessions: list[dict] = []
        self._current_session: list[dict] = []
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._load()

    def _load(self):
        try:
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._sessions = data.get("sessions", [])
        except Exception as e:
            print(f"[MEMORY LOAD ERROR] {e}")
            self._sessions = []

    def _save(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            if self._current_session:
                self._sessions.append({
                    "id": self._session_id,
                    "timestamp": datetime.now().isoformat(),
                    "messages": self._current_session,
                })
                self._current_session = []
                self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            if len(self._sessions) > MAX_SESSIONS:
                self._sessions = self._sessions[-MAX_SESSIONS:]

            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump({"sessions": self._sessions}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MEMORY SAVE ERROR] {e}")

    def add_message(self, role: str, content: str):
        self._current_session.append({"role": role, "content": content})
        if len(self._current_session) >= MAX_HISTORY:
            self._save()

    def get_recent_history(self, limit: int = MAX_HISTORY) -> list[dict]:
        history = []
        for session in self._sessions[-5:]:
            history.extend(session.get("messages", []))
        history.extend(self._current_session)
        return history[-limit:]

    def get_all_sessions(self) -> list[dict]:
        return self._sessions

    def search_memory(self, query: str) -> list[dict]:
        query_lower = query.lower()
        results = []
        for session in self._sessions:
            for msg in session.get("messages", []):
                if query_lower in msg.get("content", "").lower():
                    results.append(msg)
        for msg in self._current_session:
            if query_lower in msg.get("content", "").lower():
                results.append(msg)
        return results[-20:]

    def get_stats(self) -> dict:
        total_messages = sum(len(s.get("messages", [])) for s in self._sessions)
        total_messages += len(self._current_session)
        return {
            "total_sessions": len(self._sessions),
            "total_messages": total_messages,
            "current_session_messages": len(self._current_session),
        }

    def clear(self):
        self._sessions = []
        self._current_session = []
        self._save()

    def save_on_exit(self):
        self._save()


conversation_memory = ConversationMemory()
