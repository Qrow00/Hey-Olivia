"""Wake word detection using openwakeword (fully local, custom 'jarvis' model).

Degrades gracefully: if openwakeword/model are unavailable, falls back to
a simple energy-based trigger so the pipeline still functions.
"""

import asyncio
import os
from typing import Any, Optional


class WakeWordEngine:
    """Wake word detection with local openwakeword models."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._ww = None
        self._model = None
        self.threshold = 0.5

    async def start(self):
        try:
            import openwakeword
            self._ww = openwakeword
            if os.path.exists(self.cfg.wake_word_model):
                from openwakeword.model import Model
                self._model = Model(wakeword_models=[self.cfg.wake_word_model])
            print(f"[WakeWord] {'custom model loaded' if self._model else 'fallback: energy trigger'}")
        except Exception as e:
            print(f"[WakeWord] openwakeword unavailable ({e}); using energy trigger")
            self._ww = None
        return self

    async def stop(self):
        self._ww = None
        self._model = None

    async def process(self, audio_int16) -> bool:
        """Return True if the wake word was detected in a 16-bit PCM buffer."""
        if self._model is not None:
            loop = asyncio.get_running_loop()
            preds = await loop.run_in_executor(
                None, lambda: self._model.predict(audio_int16))
            # preds: dict of model_name -> [probability per frame]
            for probs in preds.values():
                if probs and max(probs) >= self.threshold:
                    return True
            return False
        if self._ww is None:
            # fallback: loud enough audio counts as a trigger
            peak = max((abs(int(x)) for x in audio_int16), default=0)
            return peak > 3000
        return False

    def available(self) -> bool:
        return self._model is not None or self._ww is not None
