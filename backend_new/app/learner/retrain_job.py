"""RetrainJob - background retraining of the intent classifier.

Grows with the user: accumulated feedback + taught examples are folded
into the classifier with a replay buffer (seed data is always replayed,
so the model never forgets existing intents).
"""

import asyncio
from typing import Optional

from app.learner.feedback import FeedbackStore
from app.nlu.intent_classifier import IntentClassifier
from app.nlu.training_data import SEED_INTENTS


async def retrain_from_feedback(fb_store: FeedbackStore, model_path: str) -> bool:
    """Retrain the intent classifier from feedback examples and persist it."""
    examples = await fb_store.training_examples()
    clf = IntentClassifier()
    clf.train(list(SEED_INTENTS))  # replay buffer: prevents catastrophic forgetting
    for ex in examples:
        clf.add_example(ex["text"], ex["intent"])
    clf.train()
    clf.save(model_path)
    return True


class RetrainJob:
    """Periodic background retrainer with a minimum-samples guard."""

    def __init__(self, cfg, fb_store: FeedbackStore, model_path: str):
        self.cfg = cfg
        self.fb_store = fb_store
        self.model_path = model_path
        self._task: Optional[asyncio.Task] = None

    def start(self):
        if self._task is None:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._task = loop.create_task(self._run())
            else:
                loop.run_until_complete(self._run_once())
        return self

    async def stop(self):
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self):
        try:
            while True:
                await asyncio.sleep(self.cfg.retrain_interval_s)
                await self._maybe_retrain()
        except asyncio.CancelledError:
            pass

    async def _run_once(self):
        await self._maybe_retrain()

    async def _maybe_retrain(self) -> None:
        try:
            stats = await self.fb_store.stats()
            if stats["total"] >= self.cfg.retrain_min_samples:
                await retrain_from_feedback(self.fb_store, self.model_path)
                print("[Learner] Retrained intent classifier.")
        except Exception as e:
            print(f"[Learner] Retrain error: {e}")
