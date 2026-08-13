"""FaceDB - persistent face embedding store (who is who).

Stores one or more 128/512-d embeddings per identity in SQLite.
Matching is cosine similarity against the centroid per identity.
No heavy deps: embeddings are just lists of floats.
"""

import json
import math
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

from app.memory.vector_store import cosine


class FaceDB:
    """Persistent identity -> embeddings mapping with cosine matching."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.db_path = str(Path(cfg.data_dir) / "faces.db")
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            embedding TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")
        conn.commit()
        conn.close()

    def add(self, name: str, embedding: List[float]) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO faces (name, embedding) VALUES (?, ?)",
                     (name, json.dumps(list(embedding))))
        conn.commit()
        conn.close()

    def embeddings_for(self, name: str) -> List[List[float]]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT embedding FROM faces WHERE name = ?", (name,)).fetchall()
        conn.close()
        out = []
        for (emb,) in rows:
            try:
                out.append(json.loads(emb))
            except (json.JSONDecodeError, TypeError):
                continue
        return out

    def identities(self) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT DISTINCT name FROM faces").fetchall()
        conn.close()
        return [r[0] for r in rows]

    def count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT COUNT(*) FROM faces").fetchone()
        conn.close()
        return row[0] if row else 0

    def _centroid(self, name: str) -> Optional[List[float]]:
        embs = self.embeddings_for(name)
        if not embs:
            return None
        n = len(embs)
        dim = len(embs[0])
        return [sum(e[i] for e in embs) / n for i in range(dim)]

    def match(self, embedding: List[float]) -> Tuple[str, float]:
        """Return (best_identity, score). 'unknown' when below threshold."""
        best_name, best_score = "unknown", 0.0
        for name in self.identities():
            centroid = self._centroid(name)
            if centroid is None:
                continue
            score = cosine(embedding, centroid)
            if score > best_score:
                best_name, best_score = name, score
        if best_score < self.cfg.face_match_threshold:
            return "unknown", best_score
        return best_name, best_score

    def remove(self, name: str) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM faces WHERE name = ?", (name,))
        conn.commit()
        conn.close()
