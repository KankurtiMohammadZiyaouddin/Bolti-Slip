"""
services/prisma.py
------------------
Reusable, production-oriented wrapper for the Gnani AI Prisma v3.0
Speech-to-Text API.

Verified endpoint  : https://api.vachana.ai/stt/v3
Verified parameters: model=prisma-v3.0, language_code=indic-auto, format=codemix
Auth header        : X-API-Key-ID (value from GNANI_API_KEY_ID env var)

This module is intentionally Streamlit-free so it can be used by any
part of the Bolti Slip application (CLI, web UI, batch jobs, tests).
"""

import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from backend.services.audio_converter import ensure_prisma_compatible_audio

# ---------------------------------------------------------------------------
# Constants — verified against the working test_prisma.py integration test
# ---------------------------------------------------------------------------
_API_ENDPOINT: str = "https://api.vachana.ai/stt/v3"
_MODEL: str = "prisma-v3.0"
_LANGUAGE_CODE: str = "indic-auto"
_FORMAT: str = "codemix"
_TIMEOUT_SECONDS: int = 60

# MIME types for audio formats accepted by the Gnani STT API
_AUDIO_MIME_TYPES: dict[str, str] = {
    ".wav":  "audio/wav",
    ".mp3":  "audio/mpeg",
    ".m4a":  "audio/mp4",
    ".mp4":  "audio/mp4",
    ".ogg":  "audio/ogg",
    ".flac": "audio/flac",
    ".aac":  "audio/aac",
}


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------
PrismaResult = dict[str, Any]
"""
Structured dictionary returned by PrismaService.transcribe().

Keys
----
success                  : bool        – True if the API call succeeded.
transcript               : str | None  – The recognised text.
detected_language_code   : str | None  – Language detected by the model.
model                    : str         – Model name used (prisma-v3.0).
http_status_code         : int | None  – HTTP status code from the API.
api_processing_time      : float | None– Server-reported processing time (seconds),
                                         extracted from the API response body if present.
request_elapsed_seconds  : float | None– Client-side wall-clock round-trip time (seconds).
request_id               : str | None  – Server-side request ID if provided.
error                    : str | None  – Human-readable error message (None on success).
error_type               : str | None  – Machine-readable error category (None on success).
raw_response             : dict | None – Full parsed JSON body from the API (None on failure).
"""


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------
class PrismaService:
    """
    Client for the Gnani AI Prisma v3.0 Speech-to-Text API.

    Parameters
    ----------
    env_path : Path | str | None
        Path to the .env file that holds GNANI_API_KEY_ID.
        Defaults to the project root .env and backend/.env.
    timeout : int
        Request timeout in seconds. Defaults to 60.

    Raises
    ------
    EnvironmentError
        If GNANI_API_KEY_ID is not set after loading the .env file.
    """

    def __init__(
        self,
        env_path: "Path | str | None" = None,
        timeout: int = _TIMEOUT_SECONDS,
    ) -> None:
        if env_path is not None:
            load_dotenv(dotenv_path=Path(env_path), override=False)
        else:
            project_root = Path(__file__).resolve().parent.parent.parent
            # Load root .env first, then backend/.env without overriding existing deployment env vars
            load_dotenv(dotenv_path=project_root / ".env", override=False)
            load_dotenv(dotenv_path=project_root / "backend" / ".env", override=False)

        api_key = os.getenv("GNANI_API_KEY_ID")
        if not api_key:
            raise EnvironmentError(
                "GNANI_API_KEY_ID is not set. "
                "Add it to your .env file before using PrismaService."
            )

        # Private — never surfaced in repr, logs, or error messages.
        self._api_key: str = api_key
        self._timeout: int = timeout
        self._endpoint: str = _API_ENDPOINT

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def transcribe(self, audio_path: "Path | str") -> PrismaResult:
        """
        Transcribe a single audio file using the Gnani Prisma v3.0 API.

        Parameters
        ----------
        audio_path : Path | str
            Path to the audio file to transcribe. Must exist and be
            readable. PCM WAV (16 kHz, mono, 16-bit) gives best results.

        Returns
        -------
        PrismaResult
            A dictionary with the keys described in the PrismaResult type
            alias. ``success`` is the primary status flag; inspect ``error``
            and ``error_type`` when it is False.

        Notes
        -----
        - ``api_processing_time``: extracted from the API response body when
          the server includes a processing_time / duration field.
        - ``request_elapsed_seconds``: client-side monotonic wall-clock time
          covering the full HTTP round trip.
        - The API key is never included in any returned error message.
        - A failed request does not raise; it returns ``success=False``.
        """
        audio_path = Path(audio_path)
        result = self._empty_result()

        # --- Pre-flight checks ------------------------------------------
        if not audio_path.exists():
            return self._fail(
                result,
                error=f"Audio file not found: {audio_path.name}",
                error_type="FILE_NOT_FOUND",
            )

        if not audio_path.is_file():
            return self._fail(
                result,
                error=f"Path is not a file: {audio_path.name}",
                error_type="INVALID_PATH",
            )

        # --- Build request -----------------------------------------------
        headers = {"X-API-Key-ID": self._api_key}
        form_data = {
            "model":         _MODEL,
            "language_code": _LANGUAGE_CODE,
            "format":        _FORMAT,
        }

        # --- Send request (transparently converts WebM/Opus to WAV if needed) --
        start = time.monotonic()
        try:
            with ensure_prisma_compatible_audio(audio_path) as ready_path:
                mime_type = _AUDIO_MIME_TYPES.get(ready_path.suffix.lower(), "audio/wav")
                with ready_path.open("rb") as audio_file:
                    response = requests.post(
                        self._endpoint,
                        headers=headers,
                        data=form_data,
                        files={"audio_file": (ready_path.name, audio_file, mime_type)},
                        timeout=self._timeout,
                    )
            elapsed = round(time.monotonic() - start, 3)

        except requests.exceptions.ConnectionError:
            result["request_elapsed_seconds"] = round(time.monotonic() - start, 3)
            return self._fail(
                result,
                error="Connection failed. Check your network or the API endpoint.",
                error_type="CONNECTION_ERROR",
            )

        except requests.exceptions.Timeout:
            result["request_elapsed_seconds"] = round(time.monotonic() - start, 3)
            return self._fail(
                result,
                error=f"Request timed out after {self._timeout}s.",
                error_type="TIMEOUT",
            )

        except requests.exceptions.RequestException as exc:
            result["request_elapsed_seconds"] = round(time.monotonic() - start, 3)
            return self._fail(
                result,
                error=f"Unexpected request error: {exc}",
                error_type="REQUEST_ERROR",
            )

        except Exception as exc:
            result["request_elapsed_seconds"] = round(time.monotonic() - start, 3)
            return self._fail(
                result,
                error=f"Audio processing error: {exc}",
                error_type="AUDIO_PROCESSING_ERROR",
            )

        # Record client-side elapsed time and HTTP status immediately.
        result["request_elapsed_seconds"] = elapsed
        result["http_status_code"] = response.status_code

        # --- HTTP-level errors -------------------------------------------
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            body_preview = response.text[:300]   # never contains the key
            return self._fail(
                result,
                error=f"HTTP {response.status_code}: {body_preview}",
                error_type="HTTP_ERROR",
            )

        # --- Parse JSON response -----------------------------------------
        try:
            data: dict = response.json()
        except (json.JSONDecodeError, ValueError):
            return self._fail(
                result,
                error=f"Server returned non-JSON response: {response.text[:200]}",
                error_type="INVALID_JSON",
            )

        # --- Extract fields ----------------------------------------------
        result["success"]      = True
        result["raw_response"] = data

        # Transcript — try documented key names in priority order.
        result["transcript"] = (
            data.get("transcript")
            or data.get("text")
            or data.get("result")
        )

        # Detected language
        result["detected_language_code"] = (
            data.get("detected_language_code")
            or data.get("language_code")
        )

        # Server-side request ID (key name varies across API versions)
        result["request_id"] = (
            data.get("request_id")
            or data.get("requestId")
            or data.get("id")
        )

        # Server-reported processing time — preferred over client elapsed.
        # The API may return it as seconds (float) or milliseconds (int).
        api_time = (
            data.get("processing_time")
            or data.get("processingTime")
            or data.get("duration_ms")
            or data.get("duration")
        )
        if api_time is not None:
            try:
                api_time_f = float(api_time)
                # Heuristic: values > 500 are almost certainly milliseconds.
                result["api_processing_time"] = (
                    round(api_time_f / 1000, 3) if api_time_f > 500 else round(api_time_f, 3)
                )
            except (TypeError, ValueError):
                result["api_processing_time"] = None

        return result

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def endpoint(self) -> str:
        """The API endpoint URL used by this service instance."""
        return self._endpoint

    @property
    def model(self) -> str:
        """The STT model name used for all requests."""
        return _MODEL

    @property
    def language_code(self) -> str:
        """The language_code parameter sent with every request."""
        return _LANGUAGE_CODE

    @property
    def format(self) -> str:
        """The format parameter sent with every request."""
        return _FORMAT

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _empty_result() -> PrismaResult:
        """Return a zeroed-out result dict with all expected keys present."""
        return {
            "success":                 False,
            "transcript":              None,
            "detected_language_code":  None,
            "model":                   _MODEL,
            "http_status_code":        None,
            "api_processing_time":     None,
            "request_elapsed_seconds": None,
            "request_id":              None,
            "error":                   None,
            "error_type":              None,
            "raw_response":            None,
        }

    @staticmethod
    def _fail(result: PrismaResult, *, error: str, error_type: str) -> PrismaResult:
        """Stamp a failure onto an in-progress result dict and return it."""
        result["success"]    = False
        result["error"]      = error
        result["error_type"] = error_type
        return result
