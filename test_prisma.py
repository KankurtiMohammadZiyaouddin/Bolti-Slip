"""
test_prisma.py
--------------
Isolated integration test for the Gnani AI Prisma v3.0 STT API.
Part of the Bolti Slip project.

Usage:
    1. Make sure your virtual environment is active.
    2. Install dependencies:
           pip install -r requirements.txt
    3. Add your Gnani API key to the .env file:
           GNANI_API_KEY_ID=your_actual_key_here
    4. Place test_audio.wav in the project root.
    5. Run:
           python test_prisma.py
"""

import os
import sys
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ENV_FILE = Path(__file__).parent / ".env"
AUDIO_FILE = Path(__file__).parent / "test_audio.wav"

API_ENDPOINT = "https://api.vachana.ai/stt/v3"

REQUEST_TIMEOUT_SECONDS = 60  # Generous timeout for large audio files


# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=ENV_FILE)

api_key = os.getenv("GNANI_API_KEY_ID")

if not api_key:
    print(
        "[ERROR] GNANI_API_KEY_ID is not set.\n"
        "        Please add it to your .env file:\n"
        "            GNANI_API_KEY_ID=your_actual_key_here"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Validate audio file
# ---------------------------------------------------------------------------
if not AUDIO_FILE.exists():
    print(f"[ERROR] Audio file not found: {AUDIO_FILE}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Send request
# ---------------------------------------------------------------------------
print(f"[INFO] Sending audio to Gnani AI Prisma v3.0 ...")
print(f"[INFO] Endpoint : {API_ENDPOINT}")
print(f"[INFO] Audio    : {AUDIO_FILE.name} ({AUDIO_FILE.stat().st_size} bytes)")
print("-" * 60)

headers = {
    "X-API-Key-ID": api_key,
}

form_data = {
    "model": "prisma-v3.0",
    "language_code": "indic-auto",
    "format": "codemix",
}

try:
    with AUDIO_FILE.open("rb") as audio:
        files = {
            "audio_file": (AUDIO_FILE.name, audio, "audio/wav"),
        }
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            data=form_data,
            files=files,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

except requests.exceptions.ConnectionError as e:
    print(f"[ERROR] Connection failed. Check your network or the API endpoint.\n        Detail: {e}")
    sys.exit(1)

except requests.exceptions.Timeout:
    print(
        f"[ERROR] Request timed out after {REQUEST_TIMEOUT_SECONDS}s. "
        "The server did not respond in time."
    )
    sys.exit(1)

except requests.exceptions.RequestException as e:
    print(f"[ERROR] An unexpected request error occurred: {e}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
print(f"HTTP Status : {response.status_code} {response.reason}")
print("-" * 60)

# Attempt to raise for 4xx / 5xx responses
try:
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"[ERROR] HTTP error returned by server: {e}")
    print(f"        Response body:\n{response.text}")
    sys.exit(1)

# Parse JSON body
try:
    data = response.json()
except json.JSONDecodeError:
    print("[ERROR] Could not parse JSON from the server response.")
    print(f"        Raw response:\n{response.text}")
    sys.exit(1)

# --- Key fields ---
transcript = data.get("transcript") or data.get("text") or data.get("result")
detected_language = data.get("detected_language_code") or data.get("language_code")

print(f"Transcript          : {transcript if transcript is not None else '[not found in response]'}")

if detected_language:
    print(f"Detected Language   : {detected_language}")

# --- Other metadata ---
skip_keys = {"transcript", "text", "result", "detected_language_code", "language_code"}
extras = {k: v for k, v in data.items() if k not in skip_keys}

if extras:
    print("\nOther Response Metadata:")
    for key, value in extras.items():
        print(f"  {key}: {value}")

print("-" * 60)
print("[INFO] Test complete.")
