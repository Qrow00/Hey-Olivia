import io
import tempfile
import os
import asyncio
from typing import Optional

_ffmpeg_dir = os.path.join(os.path.expanduser("~"), "ffmpeg")
if os.path.isdir(_ffmpeg_dir):
    os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

import whisper
import edge_tts
import ollama
import numpy as np
import soundfile as sf

from app.services.voice_profile_service import voice_profile_service
from app.services.personality_service import personality_service
from app.services.command_registry import command_registry
from app.services.conversation_memory import conversation_memory
from app.services.knowledge_service import knowledge_service
from app.services.settings_service import settings_service


class VoiceService:
    def __init__(self):
        self.stt_model = None
        self.tts_voice = "en-US-GuyNeural"
        self.llm_model = "llama3.2"
        self._initialized = False
        self._max_history = 15

    def _get_model(self, profile_id: str = "default") -> str:
        return settings_service.get(profile_id, "voice", "llm_model") or self.llm_model

    async def initialize(self):
        if self._initialized:
            return
        import torch
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._fp16 = self._device == "cuda"
        print(f"Loading Whisper STT model (base, {self._device})...")
        self.stt_model = whisper.load_model("base", device=self._device)
        self.llm_model = self._get_model()
        print(f"Voice service initialized, warming {self.llm_model}...")
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    ollama.chat,
                    model=self.llm_model,
                    messages=[{"role": "user", "content": "Hello"}],
                    options={"num_ctx": 2048}
                ),
                timeout=30
            )
            print(f"[LLM] {self.llm_model} warmed up")
        except Exception as e:
            print(f"[LLM] Warm-up skipped: {e}")
        self._initialized = True

    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> dict:
        if not self._initialized:
            await self.initialize()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.stt_model.transcribe,
                    tmp_path,
                    language=language,
                    fp16=self._fp16
                ),
                timeout=30
            )
            return {
                "text": result["text"],
                "language": result.get("language", language),
                "confidence": self._calculate_confidence(result)
            }
        finally:
            os.unlink(tmp_path)

    def _calculate_confidence(self, result: dict) -> float:
        segments = result.get("segments", [])
        if not segments:
            return 0.0
        avg_logprob = np.mean([s.get("avg_logprob", 0) for s in segments])
        return min(1.0, max(0.0, (avg_logprob + 1.0)))

    async def text_to_speech(self, text: str, voice: Optional[str] = None,
                              rate: int = 0, pitch: int = 0) -> bytes:
        voice = voice or self.tts_voice
        rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
        pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"{pitch}Hz"

        communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
        audio_data = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])

        return audio_data.getvalue()

    async def chat_completion(
        self,
        message: str,
        system_prompt: str = None,
        conversation_history: Optional[list] = None,
        profile_id: str = "default"
    ) -> dict:
        model = self._get_model(profile_id)
        if system_prompt is None:
            system_prompt = personality_service.get_system_prompt(profile_id=profile_id)

        messages = [{"role": "system", "content": system_prompt}]

        mem = conversation_memory.for_profile(profile_id)
        if conversation_history:
            messages.extend(conversation_history[-self._max_history:])
        else:
            history = mem.get_recent_history(self._max_history)
            if history:
                messages.extend(history)

        knowledge_context = knowledge_service.get_context_for_llm(message)
        if knowledge_context:
            messages.insert(1, {"role": "system", "content": f"Your knowledge about the user:\n{knowledge_context}\n\nUse this information naturally in your responses. Do not say 'according to my notes' or 'you told me' — just know it."})

        messages.append({"role": "user", "content": message})

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    ollama.chat,
                    model=model,
                    messages=messages,
                    options={"num_ctx": 2048}
                ),
                timeout=30
            )
        except asyncio.TimeoutError:
            print(f"[LLM] Timeout waiting for {model}")
            return {"response": "I'm taking too long to respond. Please try again.", "model": model, "done": True}
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return {"response": "I had trouble thinking just now. Please try again.", "model": model, "done": True}

        assistant_response = response["message"]["content"]
        mem.add_message("user", message)
        mem.add_message("assistant", assistant_response)

        try:
            knowledge_service.extract_and_store(message, assistant_response)
        except:
            pass

        return {
            "response": assistant_response,
            "model": model,
            "done": response.get("done", True)
        }

    async def voice_pipeline(
        self,
        audio_data: bytes,
        system_prompt: str = None,
        conversation_history: Optional[list] = None,
        tts_voice: Optional[str] = None,
        profile_id: str = "default"
    ) -> dict:
        stt_result = await self.speech_to_text(audio_data)

        llm_result = await self.chat_completion(
            message=stt_result["text"],
            system_prompt=system_prompt or personality_service.get_system_prompt(profile_id=profile_id),
            conversation_history=conversation_history,
            profile_id=profile_id,
        )

        profile = voice_profile_service.get_active_profile()
        tts_audio = await self.text_to_speech(
            text=llm_result["response"],
            voice=tts_voice or profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        return {
            "transcription": stt_result["text"],
            "confidence": stt_result["confidence"],
            "response": llm_result["response"],
            "audio": tts_audio,
            "model": llm_result["model"],
        }

    def get_status(self, profile_id: str = "default") -> dict:
        mem = conversation_memory.for_profile(profile_id)
        return {
            "initialized": self._initialized,
            "stt_model": "whisper-tiny",
            "device": getattr(self, "_device", "cpu"),
            "tts_voice": voice_profile_service.get_active_profile().name,
            "llm_model": self._get_model(profile_id),
            "conversation_length": len(mem.get_recent_history(999)),
            "personality": personality_service.get_status(profile_id=profile_id),
        }


voice_service = VoiceService()
