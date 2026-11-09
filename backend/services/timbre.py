"""
services/timbre.py
------------------
Reusable, production-oriented wrapper for the Gnani AI Timbre v3.0
Text-to-Speech API.

Documented endpoint : https://api.vachana.ai/api/v1/tts/inference
Auth header         : X-API-Key-ID (value from GNANI_API_KEY_ID env var)
Request format      : application/json
Response format     : Raw binary audio (WAV/MP3/OGG/etc.) on success;
                      JSON error body on failure.

Source: Official Gnani / Vachana.ai API documentation.

This module is intentionally Streamlit-free so it can be reused across
any part of the Bolti Slip application.
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Constants — from official Gnani Timbre v3.0 documentation
# ---------------------------------------------------------------------------
_API_ENDPOINT: str = "https://api.vachana.ai/api/v1/tts/inference"
_MODEL: str = "timbre-v3.0"
_TIMEOUT_SECONDS: int = 60

# Documented voices for Timbre v3.0
TIMBRE_VOICES: tuple[str, ...] = (
    "Shivani", "Avinash", "Lakshmi", "Kalpana", "Shubham",
    "Prakash", "Devansh", "Yashraj", "Chetana", "Vasudha",
    "Riyaa",   "Tarika",  "Harshad",
)

# Documented BCP-47 language codes supported by Timbre v3.0
TIMBRE_LANGUAGES: tuple[str, ...] = (
    "hi-IN",  # Hindi
    "en-IN",  # Indian English
    "ta-IN",  # Tamil
    "te-IN",  # Telugu
    "kn-IN",  # Kannada
    "ml-IN",  # Malayalam
    "mr-IN",  # Marathi
    "pa-IN",  # Punjabi
    "bn-IN",  # Bengali
    "gu-IN",  # Gujarati
)

# Documented audio container formats
AudioContainer = Literal["wav", "mp3", "ogg", "mulaw", "alaw", "raw"]

# Documented PCM encodings
AudioEncoding = Literal["linear_pcm", "pcm_mulaw", "pcm_alaw", "oggopus"]

# Map container → HTTP Content-Type returned by the API
_CONTAINER_CONTENT_TYPE: dict[str, str] = {
    "wav":   "audio/wav",
    "mp3":   "audio/mpeg",
    "ogg":   "audio/ogg",
    "mulaw": "audio/basic",
    "alaw":  "audio/alaw",
    "raw":   "audio/pcm",
}

# Map container → sensible file extension for saving
_CONTAINER_EXTENSION: dict[str, str] = {
    "wav":   ".wav",
    "mp3":   ".mp3",
    "ogg":   ".ogg",
    "mulaw": ".ul",
    "alaw":  ".al",
    "raw":   ".pcm",
}


# ---------------------------------------------------------------------------
# Audio config dataclass
# ---------------------------------------------------------------------------
@dataclass
class AudioConfig:
    """
    Audio output configuration for the Timbre v3.0 API.

    Attributes
    ----------
    sample_rate : int
        Output sample rate in Hz. Default: 48000.
    num_channels : int
        Number of audio channels. 1 = mono. Default: 1.
    sample_width : int
        Bytes per sample. 2 = 16-bit PCM. Default: 2.
    encoding : str
        PCM encoding type. Default: "linear_pcm".
    container : str
        Audio container/format. Default: "wav".
    """
    sample_rate:  int          = 48000
    num_channels: int          = 1
    sample_width: int          = 2
    encoding:     AudioEncoding = "linear_pcm"
    container:    AudioContainer = "wav"

    def to_dict(self) -> dict[str, Any]:
        """Serialise to the dict shape expected by the Timbre API."""
        return {
            "sample_rate":  self.sample_rate,
            "num_channels": self.num_channels,
            "sample_width": self.sample_width,
            "encoding":     self.encoding,
            "container":    self.container,
        }


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------
TimbreResult = dict[str, Any]
"""
Structured dictionary returned by TimbreService.synthesise().

Keys
----
success                  : bool        – True if audio was returned.
audio_bytes              : bytes | None– Raw audio data from the API.
audio_saved_to           : str | None  – Absolute path if saved to disk.
audio_size_bytes         : int | None  – Length of returned audio in bytes.
container                : str         – Requested audio container format.
http_status_code         : int | None  – HTTP status code from the API.
request_elapsed_seconds  : float | None– Client-side round-trip time.
error                    : str | None  – Human-readable error (None on success).
error_type               : str | None  – Machine-readable error category.
"""


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------
class TimbreService:
    """
    Client for the Gnani AI Timbre v3.0 Text-to-Speech API.

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
                "Add it to your .env file before using TimbreService."
            )

        # Private — never surfaced in repr, logs, or error messages.
        self._api_key: str = api_key
        self._timeout: int = timeout
        self._endpoint: str = _API_ENDPOINT

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------
    def synthesise(
        self,
        text: str,
        *,
        voice: str = "Devansh",
        language: str = "hi-IN",
        speed: float = 1.0,
        audio_config: "AudioConfig | None" = None,
        save_to: "Path | str | None" = None,
    ) -> TimbreResult:
        """
        Synthesise speech from text using the Gnani Timbre v3.0 API.

        Parameters
        ----------
        text : str
            The text to synthesise. Timbre v3.0 supports inline expression
            tags such as <laugh>, <pauses>, <whispers>, <excited>, <sigh>.
        voice : str
            Voice name. Must be one of the documented Timbre v3.0 voices.
            Defaults to "Devansh". See TIMBRE_VOICES for the full list.
        language : str
            BCP-47 language code. Defaults to "hi-IN" (Hindi).
            See TIMBRE_LANGUAGES for supported codes.
        speed : float
            Speech speed multiplier. 1.0 = normal. Defaults to 1.0.
        audio_config : AudioConfig | None
            Output audio configuration. Defaults to AudioConfig()
            (48000 Hz, mono, 16-bit, linear_pcm, wav container).
        save_to : Path | str | None
            If provided, the returned audio bytes are written to this path.
            The file is created (or overwritten) on success. Ignored on
            failure.

        Returns
        -------
        TimbreResult
            A dictionary with the keys described in the TimbreResult type
            alias. ``success`` is the primary status flag.

        Notes
        -----
        - The API key is never included in any returned error message.
        - A failed request does not raise; it returns ``success=False``.
        - The API response body is raw binary audio — not JSON — on success.
        """
        if not text or not text.strip():
            return self._fail(
                self._empty_result(audio_config),
                error="text must not be empty.",
                error_type="INVALID_INPUT",
            )

        if audio_config is None:
            audio_config = AudioConfig()

        result = self._empty_result(audio_config)

        # --- Build JSON request body (from official docs) ----------------
        payload: dict[str, Any] = {
            "text":         text,
            "model":        _MODEL,
            "language":     language,
            "voice":        voice,
            "speed":        speed,
            "audio_config": audio_config.to_dict(),
        }

        headers = {
            "X-API-Key-ID": self._api_key,
            "Content-Type": "application/json",
        }

        # --- Send request ------------------------------------------------
        start = time.monotonic()
        try:
            response = requests.post(
                self._endpoint,
                headers=headers,
                json=payload,
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

        result["request_elapsed_seconds"] = elapsed
        result["http_status_code"] = response.status_code

        # --- HTTP-level errors (API returns JSON error body) -------------
        if not response.ok:
            # Try to extract structured error message from the JSON body.
            error_msg = f"HTTP {response.status_code}"
            try:
                err_data = response.json()
                api_error = err_data.get("error", {})
                if isinstance(api_error, dict):
                    error_msg = (
                        f"HTTP {response.status_code} "
                        f"[{api_error.get('type', 'UNKNOWN')}]: "
                        f"{api_error.get('message', response.text[:200])}"
                    )
                elif isinstance(api_error, str):
                    error_msg = f"HTTP {response.status_code}: {api_error}"
            except (json.JSONDecodeError, ValueError):
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"

            return self._fail(result, error=error_msg, error_type="HTTP_ERROR")

        # --- Success: response body is raw audio bytes -------------------
        audio_bytes = response.content
        if not audio_bytes:
            return self._fail(
                result,
                error="API returned HTTP 200 but with an empty response body.",
                error_type="EMPTY_RESPONSE",
            )

        result["success"]          = True
        result["audio_bytes"]      = audio_bytes
        result["audio_size_bytes"] = len(audio_bytes)

        # --- Optionally save to file -------------------------------------
        if save_to is not None:
            save_path = Path(save_to)
            try:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_bytes(audio_bytes)
                result["audio_saved_to"] = str(save_path.resolve())
            except OSError as exc:
                # Save failure is non-fatal — audio_bytes still returned.
                result["audio_saved_to"] = None
                result["error"] = f"Audio received but could not be saved: {exc}"

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
        """The TTS model name used for all requests."""
        return _MODEL

    @property
    def voices(self) -> tuple[str, ...]:
        """Documented voices available for Timbre v3.0."""
        return TIMBRE_VOICES

    @property
    def languages(self) -> tuple[str, ...]:
        """Documented BCP-47 language codes supported by Timbre v3.0."""
        return TIMBRE_LANGUAGES

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _empty_result(audio_config: "AudioConfig | None") -> TimbreResult:
        """Return a zeroed-out result dict with all expected keys present."""
        container = audio_config.container if audio_config else "wav"
        return {
            "success":                 False,
            "audio_bytes":             None,
            "audio_saved_to":          None,
            "audio_size_bytes":        None,
            "container":               container,
            "http_status_code":        None,
            "request_elapsed_seconds": None,
            "error":                   None,
            "error_type":              None,
        }

    @staticmethod
    def _fail(result: TimbreResult, *, error: str, error_type: str) -> TimbreResult:
        """Stamp a failure onto an in-progress result dict and return it."""
        result["success"]    = False
        result["error"]      = error
        result["error_type"] = error_type
        return result
