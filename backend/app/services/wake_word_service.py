import asyncio
import time
import io
import tempfile
import os
from typing import Optional, Callable
from datetime import datetime, timezone

try:
    import sounddevice as sd
    _HAS_AUDIO = True
except ImportError:
    _HAS_AUDIO = False

try:
    import webrtcvad
    _HAS_VAD = True
except ImportError:
    _HAS_VAD = False

import numpy as np


class WakeWordService:
    def __init__(self):
        self._active = False
        self._wake_phrases = ["hey jarvis", "jarvis"]
        self._sensitivity = 0.5
        self._sample_rate = 16000
        self._chunk_duration = 0.5
        self._silence_threshold = 500
        self._cooldown = 3.0
        self._last_detection = 0
        self._on_wake: Optional[Callable] = None
        self._vad = None
        self._stt_model = None
        self._audio_stream = None
        self._listen_task = None

    def set_wake_callback(self, callback: Callable):
        self._on_wake = callback

    def set_wake_phrases(self, phrases: list[str]):
        self._wake_phrases = [p.lower().strip() for p in phrases if p.strip()]

    def set_sensitivity(self, value: float):
        self._sensitivity = max(0.1, min(1.0, value))

    def get_config(self) -> dict:
        return {
            "active": self._active,
            "wake_phrases": self._wake_phrases,
            "sensitivity": self._sensitivity,
            "sample_rate": self._sample_rate,
            "cooldown": self._cooldown,
        }

    async def start(self):
        if self._active:
            return {"status": "already_active"}

        if not _HAS_AUDIO:
            return {"status": "error", "message": "sounddevice not installed. Run: pip install sounddevice"}

        if not _HAS_VAD:
            return {"status": "error", "message": "webrtcvad not installed. Run: pip install webrtcvad"}

        try:
            from app.services.voice_service import voice_service
            if not voice_service._initialized:
                await voice_service.initialize()
            self._stt_model = voice_service.stt_model
        except Exception as e:
            return {"status": "error", "message": f"Could not load STT model: {e}"}

        self._vad = webrtcvad.Vad(2)
        self._active = True
        self._listen_task = asyncio.create_task(self._listen_loop())

        print("[WAKE WORD] Started listening")
        return {"status": "success", "message": "Wake word detection started"}

    async def stop(self):
        self._active = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        print("[WAKE WORD] Stopped listening")
        return {"status": "success", "message": "Wake word detection stopped"}

    def _audio_callback(self, indata, frames, time_info, status):
        if self._audio_queue is not None:
            self._audio_queue.put(bytes(indata))

    async def _listen_loop(self):
        self._audio_queue = asyncio.Queue()
        frames_per_chunk = int(self._sample_rate * self._chunk_duration)

        try:
            self._audio_stream = sd.RawInputStream(
                samplerate=self._sample_rate,
                channels=1,
                dtype="int16",
                blocksize=frames_per_chunk,
                callback=self._audio_callback,
            )
            self._audio_stream.start()
        except Exception as e:
            print(f"[WAKE WORD] Audio stream error: {e}")
            self._active = False
            return

        buffer = bytearray()
        silence_start = None
        speech_started = False

        try:
            while self._active:
                try:
                    chunk = await asyncio.wait_for(self._audio_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                is_speech = self._is_speech(chunk)

                if is_speech:
                    if silence_start is None:
                        speech_started = True
                    silence_start = None
                    buffer.extend(chunk)
                else:
                    if speech_started:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > 0.8:
                            if len(buffer) > self._sample_rate * 0.3:
                                await self._process_buffer(bytes(buffer))
                            buffer = bytearray()
                            speech_started = False
                            silence_start = None
                    else:
                        buffer = bytearray()
                        silence_start = None

                max_buffer = self._sample_rate * 10
                if len(buffer) > max_buffer * 2:
                    buffer = buffer[-max_buffer:]

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[WAKE WORD] Listen loop error: {e}")
        finally:
            if self._audio_stream:
                try:
                    self._audio_stream.stop()
                    self._audio_stream.close()
                except Exception:
                    pass

    def _is_speech(self, chunk: bytes) -> bool:
        if not self._vad:
            return False

        try:
            return self._vad.is_speech(chunk, self._sample_rate)
        except Exception:
            return False

    async def _process_buffer(self, audio_data: bytes):
        now = time.time()
        if now - self._last_detection < self._cooldown:
            return

        try:
            import whisper

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                import soundfile as sf
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                sf.write(tmp.name, audio_np, self._sample_rate)
                tmp_path = tmp.name

            try:
                device = "cuda" if self._stt_model.device.type == "cuda" else "cpu"
                result = self._stt_model.transcribe(
                    tmp_path,
                    language="en",
                    fp16=(device == "cuda"),
                )
                text = result["text"].lower().strip()

                for phrase in self._wake_phrases:
                    if phrase in text:
                        self._last_detection = time.time()
                        print(f"[WAKE WORD] Detected: '{phrase}' (full: '{text}')")

                        if self._on_wake:
                            try:
                                await self._on_wake(text)
                            except Exception as e:
                                print(f"[WAKE WORD] Callback error: {e}")
                        return
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            print(f"[WAKE WORD] Process error: {e}")


wake_word_service = WakeWordService()
