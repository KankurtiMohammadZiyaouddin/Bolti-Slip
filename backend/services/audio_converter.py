"""
backend/services/audio_converter.py
-----------------------------------
Audio format detection and conversion utility for Bolti Slip.

Gnani Prisma v3.0 STT accepts: flac, ogg, mp3, m4a, wav, aac.
Android browsers and standard MediaRecorder record in WebM/Opus (audio/webm),
which is rejected by the Gnani API (HTTP 400 UNSUPPORTED_AUDIO_FORMAT).

This module detects incoming audio containers and transparently converts
WebM / Opus and other unsupported formats to 16 kHz 16-bit mono PCM WAV
using FFmpeg before forwarding to Gnani Prisma.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

# Formats officially accepted by Gnani Prisma v3.0 API
PRISMA_SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac"}

# Magic bytes identifying EBML / WebM / Matroska containers
EBML_HEADER = b"\x1a\x45\xdf\xa3"
RIFF_HEADER = b"RIFF"


def is_ffmpeg_available() -> bool:
    """Return True if ffmpeg executable is found in system PATH."""
    return shutil.which("ffmpeg") is not None


def is_webm_audio(file_path: Path) -> bool:
    """
    Check if the file is WebM / Opus container by inspection of suffix and magic bytes.
    Never relies solely on filename suffix.
    """
    # 1. Check extension
    if file_path.suffix.lower() in {".webm", ".weba", ".opus"}:
        return True

    # 2. Check EBML magic bytes (first 4 bytes)
    try:
        with file_path.open("rb") as f:
            header = f.read(4)
            if header == EBML_HEADER:
                return True
    except OSError:
        pass

    return False


def convert_to_pcm_wav(input_path: Path, output_path: Path, timeout_seconds: int = 30) -> None:
    """
    Convert an audio file to 16 kHz, 16-bit mono PCM WAV via FFmpeg.
    This format is optimal for Gnani Prisma Indic-ASR speech recognition.
    """
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError(
            "FFmpeg executable not found in PATH. FFmpeg is required to convert "
            "mobile WebM audio to WAV for speech recognition. Please install FFmpeg."
        )

    cmd = [
        ffmpeg_bin,
        "-y",               # Overwrite output
        "-i", str(input_path),
        "-vn",              # Disable video
        "-acodec", "pcm_s16le",
        "-ar", "16000",     # 16 kHz sample rate
        "-ac", "1",         # Mono channel
        str(output_path),
    ]

    logger.info("Converting audio via FFmpeg: %s -> %s", input_path.name, output_path.name)
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )

    if proc.returncode != 0:
        err_msg = proc.stderr.decode("utf-8", errors="ignore")[:400]
        logger.error("FFmpeg conversion failed: %s", err_msg)
        raise RuntimeError(f"FFmpeg conversion failed (code {proc.returncode}): {err_msg}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("FFmpeg generated an empty or non-existent WAV file.")


@contextmanager
def ensure_prisma_compatible_audio(source_path: Path) -> Generator[Path, None, None]:
    """
    Context manager that yields an audio Path guaranteed to be in a format
    supported by Gnani Prisma v3.0.

    - If source is already supported (WAV, MP3, OGG, FLAC, M4A, AAC) and not EBML WebM:
      Yields source_path directly with zero overhead.
    - If source is WebM or any unsupported container:
      Converts to a temporary 16kHz mono PCM WAV, yields the converted path,
      and safely unlinks the temporary converted file upon exit.
    """
    source_ext = source_path.suffix.lower()
    needs_conversion = False

    # Check if format is unsupported or contains EBML WebM header
    if source_ext not in PRISMA_SUPPORTED_EXTENSIONS or is_webm_audio(source_path):
        needs_conversion = True

    if not needs_conversion:
        # File is already in a supported format; pass through directly
        yield source_path
        return

    # Create temporary WAV output file
    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_wav_path = Path(temp_wav.name)
    temp_wav.close()  # Close file descriptor immediately to avoid Windows locking

    try:
        convert_to_pcm_wav(source_path, temp_wav_path)
        yield temp_wav_path
    finally:
        # Safely clean up temporary converted file
        temp_wav_path.unlink(missing_ok=True)
