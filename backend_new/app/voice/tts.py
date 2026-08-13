"""Text-to-speech using edge-tts (lazy). Voice/prosody driven by personality
sliders. Falls back to a no-op returning nothing when unavailable.
"""

import asyncio
from typing import Any, Dict, Optional


class TextToSpeech:
    """Personality-aware TTS via edge-tts (fully local text, online voices)."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._tts = None

    async def start(self):
        try:
            import edge_tts
            self._tts = edge_tts
            print("[TTS] edge-tts ready")
        except Exception as e:
            print(f"[TTS] edge-tts unavailable ({e})")
            self._tts = None
        return self

    async def stop(self):
        self._tts = None

    async def synthesize(self, text: str, tts_params: Optional[Dict[str, Any]] = None) -> bytes:
        """Return MP3 audio bytes for the given text."""
        if self._tts is None or not text:
            return b""
        params = tts_params or {}
        voice = params.get("voice") or self.cfg.tts_voice_default
        try:
            rate = int((params.get("rate", 1.0) - 1.0) * 100)
            pitch_hz = params.get("pitch", 0.0)
            pitch = int(pitch_hz * 50)
            communicate = self._tts.Communicate(
                text, voice, rate=f"{rate:+d}%", pitch=f"{pitch:+d}Hz")
            buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.extend(chunk["data"])
            return bytes(buffer)
        except Exception as e:
            print(f"[TTS] synthesis error: {e}")
            return b""

    def available(self) -> bool:
        return self._tts is not None
