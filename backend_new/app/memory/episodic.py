"""EpisodicMemory - persistent conversation/episode log with subscribers.

SQLite-backed, replaced V3's in-memory last-5-turns. Subscribers are
notified on each turn so the WS layer can broadcast activity.
"""

import asyncio
import json
import sqlite3
from typing import Any, Callable, Dict, List, Optional


class EpisodicMemory:
    """Append-only episodic log of turns/events with change notifications."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._subscribers: List[Callable] = []
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            text TEXT NOT NULL,
            meta TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")
        conn.commit()
        conn.close()

    def subscribe(self, callback: Callable) -> None:
        self._subscribers.append(callback)

    async def add_turn(self, role: str, text: str, meta: Optional[Dict[str, Any]] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO episodes (role, text, meta) VALUES (?, ?, ?)",
            (role, text, json.dumps(meta or {})),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        for cb in self._subscribers:
            try:
                res = cb({"type": "memory_turn", "id": row_id, "role": role, "text": text,
                          "meta": meta or {}})
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                print(f"[EpisodicMemory] subscriber error: {e}")
        return row_id

    async def recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT id, role, text, meta FROM episodes ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        out = []
        for row_id, role, text, meta in reversed(rows):
            try:
                meta_obj = json.loads(meta)
            except (json.JSONDecodeError, TypeError):
                meta_obj = {}
            out.append({"id": row_id, "role": role, "text": text, "meta": meta_obj})
        return out

    async def count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()
        conn.close()
        return row[0] if row else 0
