"""
voice.py – STT and TTS helpers for the MVP.

Design choices
--------------
• Lazy-load Whisper *and* edge-tts so that importing this module never fails
  inside the GitHub Actions container (no GPU / no lib requirements).
• router is defined immediately, so FastAPI can include the routes even if
  the heavy libraries aren’t used during the test run.
"""

import io
import uuid
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/voice", tags=["voice"])

VOICE_NAME = "en-US-JennyNeural"

# -------------------------------------------------------------
# Lazy Whisper loader (avoids download on CI import)
# -------------------------------------------------------------
_stt_model = None


def _get_whisper_model():
    global _stt_model
    if _stt_model is None:
        import whisper  # local import
        _stt_model = whisper.load_model("tiny")
    return _stt_model


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.post("/stt")
async def stt(file: UploadFile):
    """Speech-to-text → {"text": "..."}"""
    if file.content_type not in ("audio/wav", "audio/x-wav", "audio/mpeg"):
        raise HTTPException(400, "Audio must be WAV or MP3")
    audio_bytes = await file.read()
    model = _get_whisper_model()
    result = model.transcribe(io.BytesIO(audio_bytes))
    return {"text": result["text"].strip()}


@router.get("/tts")
async def tts(text: str):
    """Text-to-speech: streams MP3 using edge-tts."""
    if not text:
        raise HTTPException(400, "No text")

    # local import so CI can import the module even if edge-tts deps are absent
    import edge_tts

    tts = edge_tts.Communicate(text, VOICE_NAME)
    gen = tts.stream()

    async def _iter():
        async for chunk in gen:
            if chunk["type"] == "audio":
                yield chunk["data"]

    headers = {
        "Content-Disposition": f'inline; filename="{uuid.uuid4()}.mp3"',
        "Content-Type": "audio/mpeg",
    }
    return StreamingResponse(_iter(), headers=headers)
