from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from app.services.voice_service import voice_service
import edge_tts
import io

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    system_prompt: str = "You are J.A.R.V.I.S., a helpful AI assistant."
    conversation_history: Optional[List[dict]] = None


class VoiceConfig(BaseModel):
    stt_model: str = "base"
    tts_voice: str = "en-US-GuyNeural"
    llm_model: str = "llama3.2"


@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = "en"
):
    try:
        audio_data = await audio.read()
        result = await voice_service.speech_to_text(audio_data, language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts")
async def text_to_speech(text: str, voice: Optional[str] = None):
    try:
        audio_data = await voice_service.text_to_speech(text, voice)
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    try:
        result = await voice_service.chat_completion(
            message=request.message,
            system_prompt=request.system_prompt,
            conversation_history=request.conversation_history
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline")
async def voice_pipeline(
    audio: UploadFile = File(...),
    system_prompt: str = "You are J.A.R.V.I.S., a helpful AI assistant.",
    tts_voice: Optional[str] = None
):
    try:
        audio_data = await audio.read()
        result = await voice_service.voice_pipeline(
            audio_data=audio_data,
            system_prompt=system_prompt,
            tts_voice=tts_voice
        )
        return {
            "transcription": result["transcription"],
            "confidence": result["confidence"],
            "response": result["response"],
            "model": result["model"],
            "audio_base64": result["audio"].hex()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices():
    voices = await edge_tts.list_voices()
    return {"voices": voices}


@router.post("/config")
async def update_config(config: VoiceConfig):
    voice_service.tts_voice = config.tts_voice
    voice_service.llm_model = config.llm_model
    return {"status": "updated", "config": config}
