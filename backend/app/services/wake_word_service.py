import os
import struct
import numpy as np
from typing import Optional, Callable, List

try:
    import openwakeword
    from openwakeword.model import Model as OwwModel
    _HAS_OPENWAKEWORD = True
except ImportError:
    _HAS_OPENWAKEWORD = False

FRAME_LENGTH = 1280


class WakeWordService:
    def __init__(self):
        self._active = False
        self._model: Optional[OwwModel] = None
        self._model_names: List[str] = ["hey_jarvis"]
        self._threshold = 0.5
        self._on_wake: Optional[Callable] = None
        self._sample_rate = 16000
        self._frame_length = FRAME_LENGTH

    @property
    def frame_length(self) -> int:
        return self._frame_length

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def set_wake_callback(self, callback: Callable):
        self._on_wake = callback

    def set_threshold(self, value: float):
        self._threshold = max(0.0, min(1.0, value))

    def set_keywords(self, keywords: List[str]):
        model_map = {
            "hey jarvis": "hey_jarvis",
            "jarvis": "hey_jarvis",
            "alexa": "alexa",
            "hey mycroft": "hey_mycroft",
            "mycroft": "hey_mycroft",
            "hey rhasspy": "hey_rhasspy",
        }
        self._model_names = []
        for kw in keywords:
            kw_lower = kw.lower().strip()
            mapped = model_map.get(kw_lower, kw_lower.replace(" ", "_"))
            self._model_names.append(mapped)
        self._model = None

    def get_config(self) -> dict:
        return {
            "active": self._active,
            "models": self._model_names,
            "threshold": self._threshold,
            "sample_rate": self._sample_rate,
            "frame_length": self._frame_length,
            "engine": "openWakeWord",
        }

    def _ensure_model(self):
        if self._model is not None:
            return True

        if not _HAS_OPENWAKEWORD:
            print("[WAKE WORD] openwakeword not installed")
            return False

        try:
            openwakeword.utils.download_models()
            self._model = OwwModel(
                wakeword_models=self._model_names,
                inference_framework="onnx",
            )
            print(f"[WAKE WORD] openWakeWord loaded: models={self._model_names}, threshold={self._threshold}")
            return True
        except Exception as e:
            print(f"[WAKE WORD] Model load error: {e}")
            self._model = None
            return False

    def _decode_audio(self, audio_bytes: bytes):
        if not audio_bytes:
            return None
        if len(audio_bytes) >= 44 and audio_bytes[:4] == b"RIFF":
            try:
                data_size = struct.unpack("<I", audio_bytes[40:44])[0]
                pcm = audio_bytes[44:44 + data_size]
            except Exception:
                pcm = audio_bytes
        else:
            pcm = audio_bytes
        if not pcm:
            return None
        return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

    def process_bytes(self, audio_bytes: bytes) -> bool:
        if not self._ensure_model():
            return False

        try:
            audio_np = self._decode_audio(audio_bytes)
            if audio_np is None or len(audio_np) < FRAME_LENGTH:
                return False
            prediction = self._model.predict(audio_np)

            for model_name in self._model_names:
                score = prediction.get(model_name, 0.0)
                if score > self._threshold:
                    print(f"[WAKE WORD] Detected '{model_name}' score={score:.3f}")
                    self._model.reset()
                    return True
            return False
        except Exception as e:
            print(f"[WAKE WORD] Predict error: {e}")
            return False

    async def start(self):
        if self._active:
            return {"status": "already_active"}

        if not self._ensure_model():
            return {"status": "error", "message": "Could not load openWakeWord model"}

        self._active = True
        print("[WAKE WORD] openWakeWord started")
        return {"status": "success", "message": "Wake word detection started"}

    async def stop(self):
        self._active = False
        self._model = None
        print("[WAKE WORD] openWakeWord stopped")
        return {"status": "success", "message": "Wake word detection stopped"}

    def cleanup(self):
        self._active = False
        self._model = None


wake_word_service = WakeWordService()
