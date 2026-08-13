"""VoicePipelinePlugin - Core voice pipeline composed of: Listen→STT→LLM→TTS.

Fixed-order composable flow:
1. Wake word detection (openWakeWord + Silero VAD)
2. Speech-to-Text (Whisper streaming)
3. LLM intent interpretation (direct GGUF inference)
4. Text-to-Speech (edge-tts, pre-cached voices)
"""

import asyncio
import base64
import time
from typing import Dict, Any, Optional

from app.plugins.base import BasePlugin
import numpy as np


class VoicePipelinePlugin(BasePlugin):
    """Core voice pipeline plugin implementing the composable flow:
    WakeWord → STT → LLM → TTS
    
    All state travels with the request; no global singletons.
    """
    
    name = "voice_pipeline"
    
    def __init__(self):
        super().__init__()
        self.is_listening = False
        self.wake_word_threshold = 0.5
        self.vad_threshold = 0.5
        self.min_command_duration = 0.4  # seconds
        self.max_command_duration = 12.0  # seconds
        
    async def start(self, kernel) -> None:
        """Initialize voice pipeline resources."""
        self.is_listening = True
        # In production: initialize openWakeWord, Whisper model, LLM GGUF, edge-tts
        print(f"[{self.name}] Voice pipeline started, listening=enabled")
    
    async def stop(self, kernel) -> None:
        """Clean up voice pipeline resources."""
        self.is_listening = False
        print(f"[{self.name}] Voice pipeline stopped")
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming WebSocket voice messages."""
        msg_type = message.get("type")
        
        if msg_type == "voice_chunk":
            # Process streaming audio chunk
            data = message.get("data", "")
            return await self._process_audio_chunk(data)
        
        elif msg_type == "voice_command":
            # Text command bypassing voice pipeline
            text = message.get("text", "")
            return await self._process_text_command(text)
        
        return None
    
    async def _process_audio_chunk(self, data: str) -> Optional[Dict[str, Any]]:
        """Process a base64-encoded audio chunk."""
        # Decode audio
        try:
            audio_bytes = base64.b64decode(data)
            # In production: feed to openWakeWord + Silero VAD pipeline
            # For now, simulate wake word detection
            # threshold check simulated
            return {"type": "voice_status", "is_listening": True, "wake_detected": False}
        except Exception as e:
            return {"type": "error", "message": f"Audio processing error: {e}"}
    
    async def _process_text_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Process a text command, bypassing STT."""
        # In production: LLM intent parse, command dispatcher
        # For now, simple echo
        return {
            "type": "command_result",
            "success": True,
            "result_text": f"Heard: {text}",
            "handler": "chat_response"
        }
    
    async def process_voice_turn(self, audio_base64: str) -> Dict[str, Any]:
        """Full voice pipeline: audio → text → intent → response → TTS."""
        # Stage 1: Wake word + VAD already detected ( caller ensures this)
        # Stage 2: STT - Whisper transcription
        # Stage 3: LLM intent parse
        # Stage 4: TTS response generation
        
        # Placeholder: return structure for full pipeline
        return {
            "type": "response",
            "text": "Processing voice input...",
            "audio_base64": "",
            "avatar_state": "thinking"
        }