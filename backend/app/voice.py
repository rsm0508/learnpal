"""
voice.py – STT and TTS helpers for the MVP.

Endpoints
---------
POST /voice/stt   multipart/form-data: file=<wav|mp3>  → {"text": "..."}
GET  /voice/tts   ?text=hello                          → streams MP3

Key design notes
----------------
• Whisper and edge-tts are **lazy-loaded** so this module imports cleanly
  on CI (no heavy downloads / GPU libs during import).
• WAV/MP3 bytes are decoded to a NumPy mono-float32 array via SoundFile
  before passing to Whisper.
"""

import io
import uuid
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
import soundfile as sf
import numpy as np

router = APIRouter(prefix="/voice", tags=["voice"])

VOICE_NAME = "en-US-JennyNeural"

# ──────────────────────────────────────────────────────────────────────────────
# Lazy loaders
# ──────────────────────────────────────────────────────────────────────────────
_stt_model = None


def _get_whisper_model():
    """Load Whisper tiny model the first time it’s needed."""
    global _stt_model
    if _stt_model is None:
        import whisper  # local import → avoids CI import failure
        _stt_model = whisper.load_model("tiny")
    return _stt_model


# ──────────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────────
@router.post("/stt")
async def stt(file: UploadFile):
    """Speech-to-text → {"text": "..."}"""
    if file.content_type not in ("audio/wav", "audio/x-wav", "audio/mpeg"):
        raise HTTPException(400, "Audio must be WAV or MP3")

    # read bytes
    audio_bytes = await file.read()

    # decode to mono float32 NumPy array
    try:
        data, _ = sf.read(io.BytesIO(audio_bytes), dtype="float32")
        if data.ndim > 1:                        # stereo → mono
            data = np.mean(data, axis=1)
    except Exception as exc:
        raise HTTPException(400, f"Bad audio: {exc}")

    text = _get_whisper_model().transcribe(data)["text"].strip()
    return {"text": text}


@router.get("/tts")
async def tts(text: str):
    """Text-to-speech: streams MP3 using edge-tts."""
    if not text:
        raise HTTPException(400, "No text")

    import edge_tts  # local import → safe for CI

    communicator = edge_tts.Communicate(text, VOICE_NAME)
    gen = communicator.stream()

    async def _chunks():
        async for chunk in gen:
            if chunk["type"] == "audio":
                yield chunk["data"]

    headers = {
        "Content-Disposition": f'inline; filename="{uuid.uuid4()}.mp3"',
        "Content-Type": "audio/mpeg",
    }
    return StreamingResponse(_chunks(), headers=headers)
