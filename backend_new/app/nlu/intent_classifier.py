"""IntentClassifier - pure-Python multinomial Naive Bayes, no external ML deps.

- Trains from (text, intent) examples (seed + user-taught + feedback).
- Handles unknown tokens via Laplace smoothing.
- Persists to/from JSON so the learner can retrain in the background.
- Unknown/untrained text falls back to "chat".
"""

import json
import math
import re
import string
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

_STOP = set(string.punctuation) | {"the", "a", "an", "to", "and", "or", "of", "for", "in",
                                    "on", "at", "please", "could", "can", "you", "i", "me",
                                    "my", "me", "would", "will", "that", "this", "with",
                                    "what", "is", "are", "how", "it", "be", "do", "does",
                                    "did", "was", "were", "when", "where", "who", "why"}


def tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, emit unigrams + bigrams."""
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    words = [w for w in text.split() if w and w not in _STOP]
    toks = list(words)
    toks += [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return toks


class IntentClassifier:
    """Trainable intent classifier with JSON persistence."""

    CHAT_INTENT = "chat"
    SMOOTH = 1.0
    MIN_CONFIDENCE = 0.05

    def __init__(self):
        self._class_docs: Dict[str, int] = Counter()
        self._class_feats: Dict[str, Counter] = defaultdict(Counter)
        self._vocab: set = set()
        self._examples: List[Tuple[str, str]] = []
        self.trained = False

    # --- training -----------------------------------------------------------

    def add_example(self, text: str, intent: str) -> None:
        self._examples.append((text, intent))
        self.train()

    def train(self, examples: Optional[List[Tuple[str, str]]] = None) -> None:
        if examples is not None:
            self._examples = list(examples)
        self._class_docs = Counter()
        self._class_feats = defaultdict(Counter)
        self._vocab = set()
        for text, intent in self._examples:
            feats = tokenize(text)
            self._class_docs[intent] += 1
            for f in feats:
                self._class_feats[intent][f] += 1
                self._vocab.add(f)
        self.trained = bool(self._examples)

    # --- prediction ---------------------------------------------------------

    def predict(self, text: str) -> Tuple[str, float]:
        """Return (intent, confidence). Confidence 0.0 when untrained."""
        if not self.trained:
            return self.CHAT_INTENT, 0.0

        feats = tokenize(text)
        if not feats:
            return self.CHAT_INTENT, 0.0

        total_docs = sum(self._class_docs.values())
        vocab_size = len(self._vocab)
        n_classes = len(self._class_docs)
        prior_alpha = 1.0
        scores = {}
        for cls in self._class_docs:
            log_prior = math.log((self._class_docs[cls] + prior_alpha)
                                 / (total_docs + prior_alpha * n_classes))
            cls_feats = self._class_feats[cls]
            cls_total = sum(cls_feats.values())
            log_lik = 0.0
            for f in feats:
                count = cls_feats.get(f, 0)
                log_lik += math.log((count + self.SMOOTH) / (cls_total + self.SMOOTH * vocab_size))
            scores[cls] = log_prior + log_lik

        # length normalization (short commands shouldn't be punished)
        best_cls = max(scores, key=scores.get)
        raw_best = scores[best_cls]
        best = raw_best / max(1, len(feats))

        # softmax-style confidence against the runner-up
        if len(scores) > 1:
            second = sorted(scores.values(), reverse=True)[1]
        else:
            second = raw_best
        conf = 1.0 / (1.0 + math.exp(second - raw_best))

        if conf < self.MIN_CONFIDENCE:
            return self.CHAT_INTENT, conf
        return best_cls, conf

    # --- persistence --------------------------------------------------------

    def save(self, path: str) -> None:
        data = {
            "examples": self._examples,
            "class_docs": dict(self._class_docs),
            "class_feats": {k: dict(v) for k, v in self._class_feats.items()},
            "vocab": sorted(self._vocab),
            "trained": self.trained,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._examples = [tuple(e) for e in data.get("examples", [])]
        self._class_docs = Counter(data.get("class_docs", {}))
        self._class_feats = defaultdict(Counter, {
            k: Counter(v) for k, v in data.get("class_feats", {}).items()
        })
        self._vocab = set(data.get("vocab", []))
        self.trained = data.get("trained", False)

    @property
    def example_count(self) -> int:
        return len(self._examples)

    @property
    def intents(self) -> List[str]:
        return sorted(self._class_docs.keys())
