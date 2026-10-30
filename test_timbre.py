"""
test_timbre.py
--------------
Integration test for the Gnani AI Timbre v3.0 Text-to-Speech REST API.

Official endpoint : https://api.vachana.ai/api/v1/tts/inference
Auth header       : X-API-Key-ID (read from .env via GNANI_API_KEY_ID)
Model             : timbre-v3.0
Voice             : Devansh
Language          : hi-IN

The REST API returns raw binary audio on HTTP 200.
No SSE parsing. No Base64 decoding.

Usage:
    ./.venv/Scripts/Activate.ps1
    python test_timbre.py
"""

import os
import sys
from pathlib import Path

# Ensure stdout can handle Unicode (Devanagari) on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-16"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ENV_FILE    = Path(__file__).parent / ".env"
OUTPUT_FILE = Path(__file__).parent / "test_timbre_output.wav"

API_ENDPOINT = "https://api.vachana.ai/api/v1/tts/inference"
MODEL        = "timbre-v3.0"
VOICE        = "Devansh"
LANGUAGE     = "hi-IN"
SPEED        = 1.0
TIMEOUT_S    = 60

TEST_TEXT = (
    "आपका रिपेयर टिकट सफलतापूर्वक तैयार हो गया है। "
    "कृपया विवरण जांच लें। धन्यवाद!"
)

AUDIO_CONFIG = {
    "encoding":     "linear_pcm",
    "container":    "wav",
    "num_channels": 1,
    "sample_rate":  48000,
    "sample_width": 2,
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 65)
    print("  Gnani AI Timbre v3.0 — REST TTS Integration Test")
    print("=" * 65)

    # 1. Load API key securely
    load_dotenv(dotenv_path=ENV_FILE)
    api_key = os.getenv("GNANI_API_KEY_ID")
    if not api_key:
        print(
            "[ERROR] GNANI_API_KEY_ID is not set.\n"
            "        Add it to .env: GNANI_API_KEY_ID=your_key"
        )
        sys.exit(1)

    print(f"  Endpoint     : {API_ENDPOINT}")
    print(f"  Model        : {MODEL}")
    print(f"  Voice        : {VOICE}")
    print(f"  Language     : {LANGUAGE}")
    print(f"  Speed        : {SPEED}")
    print(f"  Sample Rate  : {AUDIO_CONFIG['sample_rate']} Hz")
    print(f"  Container    : {AUDIO_CONFIG['container']}")
    print(f"  Output File  : {OUTPUT_FILE.name}")
    print(f"  Text         : \"{TEST_TEXT}\"")
    print("-" * 65)

    # 2. Build request
    headers = {
        "X-API-Key-ID": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text":         TEST_TEXT,
        "model":        MODEL,
        "voice":        VOICE,
        "language":     LANGUAGE,
        "speed":        SPEED,
        "audio_config": AUDIO_CONFIG,
    }

    # 3. Send request
    print("[INFO] Sending POST request...")
    try:
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=TIMEOUT_S,
        )
    except requests.exceptions.ConnectionError as exc:
        print(f"[ERROR] Connection failed: {exc}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timed out after {TIMEOUT_S}s.")
        sys.exit(1)
    except requests.exceptions.RequestException as exc:
        print(f"[ERROR] Request error: {exc}")
        sys.exit(1)

    # 4. Report HTTP response details
    content_type   = response.headers.get("content-type", "unknown")
    response_bytes = len(response.content)

    print(f"  HTTP Status  : {response.status_code} {response.reason}")
    print(f"  Content-Type : {content_type}")
    print(f"  Response Size: {response_bytes:,} bytes")
    print("-" * 65)

    # 5. Handle HTTP errors
    if not response.ok:
        if response.status_code in (401, 403):
            print(
                f"[ERROR] Authentication failed (HTTP {response.status_code}).\n"
                "        Verify GNANI_API_KEY_ID is valid and has Timbre v3.0 access."
            )
        elif response.status_code in (402, 429):
            print(
                f"[ERROR] Quota or rate limit exceeded (HTTP {response.status_code}).\n"
                "        Check your Gnani developer account credits."
            )
        else:
            body_preview = response.text[:400]
            print(f"[ERROR] Server returned HTTP {response.status_code}:\n        {body_preview}")
        sys.exit(1)

    # 6. Validate raw binary response
    audio_bytes = response.content

    if not audio_bytes:
        print("[ERROR] API returned HTTP 200 but an empty response body.")
        sys.exit(1)

    if audio_bytes[:4] != b"RIFF" or audio_bytes[8:12] != b"WAVE":
        print(
            f"[ERROR] Response does not start with a valid WAV (RIFF/WAVE) header.\n"
            f"        First 16 bytes: {audio_bytes[:16].hex()}\n"
            f"        Response may be an error JSON or unexpected format."
        )
        # Print truncated body for debugging (will not contain the key)
        try:
            preview = response.json()
        except Exception:
            preview = response.text[:200]
        print(f"        Body preview: {preview}")
        sys.exit(1)

    # 7. Save to disk
    try:
        OUTPUT_FILE.write_bytes(audio_bytes)
    except OSError as exc:
        print(f"[ERROR] Could not write output file: {exc}")
        sys.exit(1)

    # 8. Verify saved file
    saved_size = OUTPUT_FILE.stat().st_size
    if saved_size == 0:
        print("[ERROR] Output file was written but is empty.")
        sys.exit(1)

    print("  WAV Header   : RIFF/WAVE — Valid")
    print(f"  Saved To     : {OUTPUT_FILE.resolve()}")
    print(f"  File Size    : {saved_size:,} bytes ({saved_size / 1024:.1f} KB)")
    print()
    print("=" * 65)
    print("  SUCCESS — Timbre v3.0 audio generated and saved.")
    print("=" * 65)
    print()
    print("Play the audio:")
    print("  (New-Object Media.SoundPlayer 'test_timbre_output.wav').PlaySync()")


if __name__ == "__main__":
    main()
