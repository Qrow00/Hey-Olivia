"""NLUPipeline - deterministic, LLM-free command understanding.

Route order (replaces V3's regex -> LLM-JSON -> chat pipeline):
  1. Fast-path regex (instant, <10ms, highest confidence)
  2. Trainable intent classifier (pure Python, ~1ms)
  3. Fallback to "chat" (conversational response, no command)

Entities are extracted deterministically in both command paths.
"""

import asyncio
import os
from typing import Dict, List, Optional, Tuple

from app.nlu.entity_extractor import extract_entities
from app.nlu.intent_classifier import IntentClassifier
from app.nlu.patterns import match_fast
from app.nlu.training_data import SEED_INTENTS


class NLUPipeline:
    """Command interpretation: regex fast-path -> classifier -> chat."""

    def __init__(self, classifier: Optional[IntentClassifier] = None,
                 model_path: Optional[str] = None):
        self.model_path = model_path
        if classifier is not None:
            self.classifier = classifier
        else:
            self.classifier = IntentClassifier()
            if model_path and os.path.exists(model_path):
                try:
                    self.classifier.load(model_path)
                    print(f"[NLU] Loaded classifier from {model_path} "
                          f"({self.classifier.example_count} examples).")
                except Exception as e:
                    print(f"[NLU] Classifier load failed ({e}); training from seeds.")
                    self.classifier.train(SEED_INTENTS)
            else:
                self.classifier.train(SEED_INTENTS)
        self._teach_buffer: List[Tuple[str, str]] = []

    async def process(self, text: str) -> Dict[str, object]:
        """Return {intent, params, source, confidence, text}."""
        text = (text or "").strip()
        if not text:
            return {"intent": "chat", "params": {}, "source": "chat",
                    "confidence": 0.0, "text": text}

        fast = match_fast(text)
        if fast:
            params = {**extract_entities(text, fast["intent"]), **fast["params"]}
            return {
                "intent": fast["intent"],
                "params": params,
                "source": "regex",
                "confidence": fast["confidence"],
                "text": text,
            }

        intent, confidence = self.classifier.predict(text)
        if intent == self.classifier.CHAT_INTENT:
            return {"intent": "chat", "params": {}, "source": "chat",
                    "confidence": confidence, "text": text}

        params = extract_entities(text, intent)
        return {"intent": intent, "params": params, "source": "classifier",
                "confidence": confidence, "text": text}

    async def teach(self, text: str, intent: str) -> bool:
        """Add a user-taught (utterance -> intent) example to the classifier."""
        if not text or not intent:
            return False
        self.classifier.add_example(text, intent)
        self.classifier.train()
        self._teach_buffer.append((text, intent))
        self.save()
        return True

    def save(self) -> None:
        """Persist the classifier so learned lessons survive a restart."""
        if self.model_path:
            try:
                self.classifier.save(self.model_path)
            except Exception as e:
                print(f"[NLU] Classifier save failed: {e}")

    def buffered_teaches(self) -> List[Tuple[str, str]]:
        return list(self._teach_buffer)

    def clear_teach_buffer(self) -> None:
        self._teach_buffer.clear()
