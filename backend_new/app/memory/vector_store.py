"""VectorStore - lightweight pure-Python embedding store with cosine search.

Stores (id, text, vector) and persists to JSON. Used for RAG memory,
face embeddings are stored separately in FaceDB. No numpy/faiss required;
all operations are plain Python math so it runs anywhere.
"""

import json
import math
import os
from typing import Dict, List, Optional, Tuple


def cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors (plain Python)."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-12
    nb = math.sqrt(sum(y * y for y in b)) or 1e-12
    return dot / (na * nb)


class VectorStore:
    """Persistent vector store with cosine similarity search."""

    def __init__(self, path: str):
        self.path = path
        self._items: Dict[str, Dict] = {}

    def add(self, doc_id: str, text: str, vector: List[float], meta: Optional[Dict] = None) -> None:
        self._items[doc_id] = {"id": doc_id, "text": text, "vector": list(vector),
                               "meta": meta or {}}
        self.save()

    def get(self, doc_id: str) -> Optional[Dict]:
        return self._items.get(doc_id)

    def search(self, vector: List[float], k: int = 5) -> List[Tuple[str, float]]:
        scored = [(i, cosine(vector, item["vector"])) for i, item in self._items.items()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def remove(self, doc_id: str) -> bool:
        if doc_id in self._items:
            del self._items[doc_id]
            self.save()
            return True
        return False

    def count(self) -> int:
        return len(self._items)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._items, f, ensure_ascii=False)

    def load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._items = json.load(f)
