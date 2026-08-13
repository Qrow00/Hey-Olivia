"""Text-to-speech. Three providers:
- piper: Piper VITS (ONNX) on DirectML GPU. Fast (~7x real-time on GTX 1050),
         local, JARVIS-like en_GB-alan voice. Default.
- kokoro: Kokoro-82M ONNX (CPU only). Natural JARVIS-like bm_george voice,
          ~real-time on CPU.
- edge: edge-tts (fast, online, good quality).

Selected via JARVIS_TTS_PROVIDER. Falls back: piper -> kokoro -> edge.
"""

import asyncio
import io
from typing import Any, Dict, Optional


class TextToSpeech:
    """Personality-aware TTS with DirectML Piper (default), Kokoro, or edge-tts."""

    def __init__(self, cfg):
        self.cfg = cfg
        self._tts = None
        self._kokoro = None
        self._piper = None
        self._provider = ""
        self._errors = {}

    async def start(self):
        try:
            import edge_tts

            self._tts = edge_tts
        except Exception as e:
            self._errors["edge"] = str(e)
        provider = self.cfg.tts_provider
        if provider == "piper" and await self._load_piper():
            self._provider = "piper"
            print(f"[TTS] piper ready (DML GPU)")
        elif provider == "kokoro" and await self._load_kokoro():
            self._provider = "kokoro"
            print(f"[TTS] kokoro ready ({self.cfg.tts_kokoro_voice})")
        elif self._tts is not None:
            self._provider = "edge"
            print("[TTS] edge-tts ready")
        else:
            print(f"[TTS] no provider available: {self._errors}")
        return self

    async def stop(self):
        self._tts = None
        self._kokoro = None
        self._piper = None

    async def _load_piper(self) -> bool:
        try:
            import json

            import onnxruntime as ort
            from piper import PiperConfig, PiperVoice

            model = self.cfg.tts_piper_model
            sess = ort.InferenceSession(
                model, providers=["DmlExecutionProvider", "CPUExecutionProvider"])
            config = PiperConfig.from_dict(
                json.load(open(model + ".json", encoding="utf-8")))
            self._piper = PiperVoice(sess, config)
            await self._warmup(self._piper)
            return True
        except Exception as e:
            self._errors["piper"] = str(e)
            return False

    async def _warmup(self, voice) -> None:
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: voice.synthesize_wav(
                    "Hello.", _open_wave(io.BytesIO())) and None,
            )
        except Exception:
            pass

    async def _load_kokoro(self) -> bool:
        try:
            from kokoro_onnx import Kokoro

            self._kokoro = Kokoro(
                self.cfg.tts_kokoro_model, self.cfg.tts_kokoro_voices)
            return True
        except Exception as e:
            self._errors["kokoro"] = str(e)
            return False

    async def synthesize(self, text: str, tts_params: Optional[Dict[str, Any]] = None) -> bytes:
        """Return audio bytes (WAV from piper/kokoro, MP3 from edge)."""
        if not text:
            return b""
        params = tts_params or {}
        if self._provider == "piper":
            return await self._synthesize_piper(text, params)
        if self._provider == "kokoro":
            return await self._synthesize_kokoro(text, params)
        if self._provider == "edge":
            return await self._synthesize_edge(text, params)
        return b""

    async def _synthesize_edge(self, text: str, params: Dict[str, Any]) -> bytes:
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
            print(f"[TTS] edge synthesis error: {e}")
            return b""

    async def _synthesize_kokoro(self, text: str, params: Dict[str, Any]) -> bytes:
        try:
            speed = params.get("rate", 1.0)
            voice = self.cfg.tts_kokoro_voice
            loop = asyncio.get_running_loop()
            samples, sr = await loop.run_in_executor(
                None,
                lambda: self._kokoro.create(text, voice=voice, speed=speed),
            )
            import numpy as np

            pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
            return _wav_bytes(pcm.tobytes(), sr)
        except Exception as e:
            print(f"[TTS] kokoro synthesis error: {e}")
            return b""

    async def _synthesize_piper(self, text: str, params: Dict[str, Any]) -> bytes:
        try:
            from piper import SynthesisConfig

            rate = params.get("rate", 1.0)
            energy = params.get("energy", 0.5)
            sarcasm = params.get("sarcasm", 0.5)
            length_scale = max(0.7, min(1.3, 1.15 / rate))
            noise_scale = 0.667 + energy * 0.18 + sarcasm * 0.1
            buf = io.BytesIO()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self._piper.synthesize_wav(
                    text, _open_wave(buf),
                    syn_config=SynthesisConfig(
                        length_scale=length_scale,
                        noise_scale=noise_scale,
                        volume=params.get("volume", 1.0),
                    ),
                ),
            )
            return buf.getvalue()
        except Exception as e:
            print(f"[TTS] piper synthesis error: {e}")
            return b""

    def available(self) -> bool:
        return self._provider != ""

    def info(self) -> Dict[str, str]:
        if not self.available():
            return {"provider": "none", "available": "false", "voice": ""}
        if self._provider == "piper":
            return {"provider": "piper", "available": "true", "voice": "en_GB-alan-medium"}
        if self._provider == "kokoro":
            return {"provider": "kokoro", "available": "true",
                    "voice": self.cfg.tts_kokoro_voice}
        return {"provider": "edge", "available": "true",
                "voice": self.cfg.tts_voice_default}


def _open_wave(buf):
    import wave

    return wave.open(buf, "wb")


def _wav_bytes(pcm: bytes, sample_rate: int) -> bytes:
    import struct

    byte_rate = sample_rate * 2
    data_size = len(pcm)
    header = b"RIFF" + struct.pack("<I", 36 + data_size) + b"WAVE"
    header += b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, byte_rate, 2, 16)
    header += b"data" + struct.pack("<I", data_size)
    return header + pcm
