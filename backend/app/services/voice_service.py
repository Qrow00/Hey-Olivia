import io
import tempfile
import os
from typing import Optional
import whisper
import edge_tts
import ollama
import numpy as np
import soundfile as sf

from app.services.voice_profile_service import voice_profile_service
from app.services.personality_service import personality_service
from app.services.command_registry import command_registry


class VoiceService:
    def __init__(self):
        self.stt_model = None
        self.tts_voice = "en-US-GuyNeural"
        self.llm_model = "llama3.2"
        self._initialized = False
        self._conversation_history: list[dict] = []
        self._max_history = 20

    async def initialize(self):
        if self._initialized:
            return
        print("Loading Whisper STT model...")
        self.stt_model = whisper.load_model("base")
        print("Voice service initialized")
        self._initialized = True

    async def speech_to_text(self, audio_data: bytes, language: str = "en") -> dict:
        if not self._initialized:
            await self.initialize()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            result = self.stt_model.transcribe(
                tmp_path,
                language=language,
                fp16=False
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
        conversation_history: Optional[list] = None
    ) -> dict:
        if system_prompt is None:
            system_prompt = personality_service.get_system_prompt()

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": message})

        response = ollama.chat(
            model=self.llm_model,
            messages=messages
        )

        return {
            "response": response["message"]["content"],
            "model": self.llm_model,
            "done": response.get("done", True)
        }

    async def voice_pipeline(
        self,
        audio_data: bytes,
        system_prompt: str = None,
        conversation_history: Optional[list] = None,
        tts_voice: Optional[str] = None
    ) -> dict:
        stt_result = await self.speech_to_text(audio_data)

        llm_result = await self.chat_completion(
            message=stt_result["text"],
            system_prompt=system_prompt or personality_service.get_system_prompt(),
            conversation_history=conversation_history or self._conversation_history[-self._max_history:]
        )

        profile = voice_profile_service.get_active_profile()
        tts_audio = await self.text_to_speech(
            text=llm_result["response"],
            voice=tts_voice or profile.voice,
            rate=profile.rate,
            pitch=profile.pitch,
        )

        self._conversation_history.append({"role": "user", "content": stt_result["text"]})
        self._conversation_history.append({"role": "assistant", "content": llm_result["response"]})

        return {
            "transcription": stt_result["text"],
            "confidence": stt_result["confidence"],
            "response": llm_result["response"],
            "audio": tts_audio,
            "model": llm_result["model"],
        }

    def get_status(self) -> dict:
        return {
            "initialized": self._initialized,
            "stt_model": "whisper-base",
            "tts_voice": voice_profile_service.get_active_profile().name,
            "llm_model": self.llm_model,
            "conversation_length": len(self._conversation_history),
            "personality": personality_service.get_status(),
        }


voice_service = VoiceService()
