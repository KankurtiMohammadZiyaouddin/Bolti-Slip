"""
backend/routers/transcription.py
---------------------------------
POST /api/transcribe
  - Accepts an audio file upload (UploadFile)
  - Saves to a temp file
  - Delegates to PrismaService.transcribe()
  - Returns a TranscribeResponse JSON
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from backend.services.prisma import PrismaService
from backend.models.ticket import TranscribeResponse

router = APIRouter(prefix="/api", tags=["transcription"])

# Service is initialised once at import time.
# PrismaService reads GNANI_API_KEY_ID from backend/.env (two levels up from
# backend/services/prisma.py → backend/.env).
_prisma = PrismaService()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Transcribe an uploaded audio file using Gnani Prisma v3.0.

    Accepts any audio format supported by the API; PCM WAV (16 kHz, mono,
    16-bit) gives the best results.

    Returns a JSON body with the transcript and metadata.
    """
    # Save upload to a named temp file so PrismaService can open it by path.
    suffix = Path(audio_file.filename or "audio.wav").suffix or ".wav"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        shutil.copyfileobj(audio_file.file, tmp)

    try:
        # PrismaService.transcribe() is synchronous (requests library).
        # Run it in a thread pool so we don't block the event loop.
        result = await asyncio.to_thread(_prisma.transcribe, tmp_path)
    finally:
        # Always clean up the temp file.
        tmp_path.unlink(missing_ok=True)

    # Strip the raw_response (large, internal) before returning.
    return {
        "success":                 result["success"],
        "transcript":              result["transcript"],
        "detected_language_code":  result["detected_language_code"],
        "model":                   result["model"],
        "http_status_code":        result["http_status_code"],
        "api_processing_time":     result["api_processing_time"],
        "request_elapsed_seconds": result["request_elapsed_seconds"],
        "error":                   result["error"],
        "error_type":              result["error_type"],
    }
