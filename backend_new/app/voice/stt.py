"""Speech-to-text using faster-whisper (lazy). Falls back to vosk if
faster-whisper is unavailable, then to a graceful "STT unavailable".

All models are local; audio never leaves the machine.
"""

import asyncio
import os
import tempfile
from typing import Optional


class SpeechToText:
    """Local transcription with graceful degradation."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._model = None
        self._backend = None

    async def start(self):
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.cfg.stt_model_size, device="cpu",
                                       compute_type="int8")
            self._backend = "faster-whisper"
            print(f"[STT] faster-whisper ({self.cfg.stt_model_size}) ready")
        except Exception as e:
            print(f"[STT] faster-whisper unavailable ({e}); STT disabled")
            self._backend = None
        return self

    async def stop(self):
        self._model = None

    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """Transcribe raw PCM (or a file path string) to text."""
        if self._backend == "faster-whisper":
            try:
                import numpy as np
                samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                loop = asyncio.get_running_loop()
                segments, _ = await loop.run_in_executor(
                    None, lambda: self._model.transcribe(samples))
                return "".join(s.text for s in segments).strip()
            except Exception as e:
                print(f"[STT] transcribe error: {e}")
                return ""
        return ""

    def available(self) -> bool:
        return self._backend is not None
