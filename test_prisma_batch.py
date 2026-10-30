"""
test_prisma_batch.py
--------------------
Batch integration test for the Gnani AI Prisma v3.0 STT API.
Tests test_01.wav through test_05.wav individually and prints a summary table.

Uses the same verified endpoint, auth method, model and parameters as test_prisma.py.
Part of the Bolti Slip project.

Usage:
    1. Activate the virtual environment:
           ./.venv/Scripts/Activate.ps1
    2. Ensure GNANI_API_KEY_ID is set in .env
    3. Place test_01.wav through test_05.wav in the project root.
    4. Run:
           python test_prisma_batch.py
"""

import os
import sys
import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration — identical to the verified test_prisma.py settings
# ---------------------------------------------------------------------------
ENV_FILE        = Path(__file__).parent / ".env"
API_ENDPOINT    = "https://api.vachana.ai/stt/v3"
MODEL           = "prisma-v3.0"
LANGUAGE_CODE   = "indic-auto"
FORMAT          = "codemix"
TIMEOUT_SECONDS = 60

AUDIO_FILES = [Path(__file__).parent / f"test_0{i}.wav" for i in range(1, 6)]

# ---------------------------------------------------------------------------
# Load environment
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=ENV_FILE)
api_key = os.getenv("GNANI_API_KEY_ID")

if not api_key:
    print(
        "[ERROR] GNANI_API_KEY_ID is not set.\n"
        "        Add it to your .env file:\n"
        "            GNANI_API_KEY_ID=your_actual_key_here"
    )
    sys.exit(1)

HEADERS = {"X-API-Key-ID": api_key}
FORM_DATA = {"model": MODEL, "language_code": LANGUAGE_CODE, "format": FORMAT}


# ---------------------------------------------------------------------------
# Helper — test a single audio file
# ---------------------------------------------------------------------------
def test_single(audio_path: Path) -> dict:
    """
    Send one audio file to the Gnani API and return a result dict with:
        file, status, transcript, detected_language, elapsed_s, error, extras
    """
    result = {
        "file":              audio_path.name,
        "status":            None,
        "transcript":        None,
        "detected_language": None,
        "elapsed_s":         None,
        "error":             None,
        "extras":            {},
    }

    if not audio_path.exists():
        result["error"] = "File not found"
        return result

    start = time.monotonic()

    try:
        with audio_path.open("rb") as f:
            response = requests.post(
                API_ENDPOINT,
                headers=HEADERS,
                data=FORM_DATA,
                files={"audio_file": (audio_path.name, f, "audio/wav")},
                timeout=TIMEOUT_SECONDS,
            )
        result["elapsed_s"] = round(time.monotonic() - start, 2)
        result["status"]    = response.status_code

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            return result

        try:
            data = response.json()
        except json.JSONDecodeError:
            result["error"] = f"Invalid JSON — raw: {response.text[:200]}"
            return result

        result["transcript"]        = (
            data.get("transcript") or data.get("text") or data.get("result")
        )
        result["detected_language"] = (
            data.get("detected_language_code") or data.get("language_code")
        )

        # Capture any extra metadata (exclude primary fields)
        skip = {"transcript", "text", "result", "detected_language_code", "language_code"}
        result["extras"] = {k: v for k, v in data.items() if k not in skip}

    except requests.exceptions.ConnectionError:
        result["elapsed_s"] = round(time.monotonic() - start, 2)
        result["error"]     = "Connection error — check network or endpoint"

    except requests.exceptions.Timeout:
        result["elapsed_s"] = round(time.monotonic() - start, 2)
        result["error"]     = f"Timeout after {TIMEOUT_SECONDS}s"

    except requests.exceptions.RequestException as e:
        result["elapsed_s"] = round(time.monotonic() - start, 2)
        result["error"]     = f"Request error: {e}"

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    total = len(AUDIO_FILES)
    print("=" * 70)
    print(f"  Gnani AI Prisma v3.0 — Batch Test  ({total} files)")
    print(f"  Endpoint : {API_ENDPOINT}")
    print(f"  Model    : {MODEL}  |  Language : {LANGUAGE_CODE}  |  Format : {FORMAT}")
    print("=" * 70)

    results = []

    for idx, audio_path in enumerate(AUDIO_FILES, start=1):
        print(f"\n[{idx}/{total}] Testing: {audio_path.name}")
        print("-" * 60)

        result = test_single(audio_path)
        results.append(result)

        if result["error"]:
            print(f"  Status   : {result['status'] or 'N/A'}")
            print(f"  ERROR    : {result['error']}")
        else:
            print(f"  Status   : {result['status']}")
            print(f"  Time     : {result['elapsed_s']}s")
            print(f"  Language : {result['detected_language'] or 'N/A'}")
            print(f"  Transcript: {result['transcript']}")
            if result["extras"]:
                print("  Extras:")
                for k, v in result["extras"].items():
                    print(f"    {k}: {v}")

    # -----------------------------------------------------------------------
    # Summary table
    # -----------------------------------------------------------------------
    print("\n")
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    col_w = {"file": 14, "status": 7, "time": 7, "lang": 14, "result": 28}
    header = (
        f"  {'File':<{col_w['file']}}"
        f"{'Status':<{col_w['status']}}"
        f"{'Time(s)':<{col_w['time']}}"
        f"{'Language':<{col_w['lang']}}"
        f"{'Transcript / Error':<{col_w['result']}}"
    )
    print(header)
    print("  " + "-" * (sum(col_w.values())))

    passed = 0
    for r in results:
        if r["error"]:
            outcome = f"ERR: {r['error']}"[:col_w["result"]]
        else:
            passed += 1
            transcript_preview = (r["transcript"] or "")[:col_w["result"]]
            outcome = transcript_preview

        status_str = str(r["status"]) if r["status"] else "N/A"
        time_str   = str(r["elapsed_s"]) if r["elapsed_s"] is not None else "N/A"
        lang_str   = (r["detected_language"] or "N/A") if not r["error"] else "N/A"

        print(
            f"  {r['file']:<{col_w['file']}}"
            f"{status_str:<{col_w['status']}}"
            f"{time_str:<{col_w['time']}}"
            f"{lang_str:<{col_w['lang']}}"
            f"{outcome}"
        )

    print("  " + "-" * (sum(col_w.values())))
    print(f"\n  Passed: {passed}/{total}   Failed: {total - passed}/{total}")
    print("=" * 70)


if __name__ == "__main__":
    main()
