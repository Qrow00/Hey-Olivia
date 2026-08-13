"""FeedbackStore - user feedback on agent responses.

Every response can be rated (good/bad/teach). Bad/teach entries with a
note or correction become new training examples for the intent classifier
(the teachable layer).
"""

import asyncio
import json
import sqlite3
from typing import Any, Dict, List, Optional


class FeedbackStore:
    """Persistent feedback log feeding the retraining pipeline."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            intent TEXT NOT NULL,
            rating TEXT NOT NULL,
            note TEXT DEFAULT '',
            correction TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")
        conn.commit()
        conn.close()

    async def record(self, text: str, intent: str, rating: str,
                     note: str = "", correction: str = "") -> int:
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO feedback (text, intent, rating, note, correction) VALUES (?, ?, ?, ?, ?)",
            (text, intent, rating, note, correction),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    async def stats(self) -> Dict[str, int]:
        conn = sqlite3.connect(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        good = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating='good'").fetchone()[0]
        bad = conn.execute("SELECT COUNT(*) FROM feedback WHERE rating='bad'").fetchone()[0]
        conn.close()
        return {"total": total, "good": good, "bad": bad}

    async def training_examples(self, limit: int = 200) -> List[Dict[str, str]]:
        """Entries usable for retraining (explicit teaches + corrections)."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            """SELECT text, intent, correction FROM feedback
               WHERE correction != '' OR rating IN ('bad', 'teach')
               ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        conn.close()
        examples = []
        for text, intent, correction in rows:
            examples.append({"text": text, "intent": correction or intent})
        return examples

    async def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT text, intent, rating, note, created_at FROM feedback ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [{"text": r[0], "intent": r[1], "rating": r[2], "note": r[3], "created_at": r[4]}
                for r in rows]
