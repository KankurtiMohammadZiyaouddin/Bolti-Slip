"""
tests/test_audio_compatibility.py
---------------------------------
Comprehensive regression test suite for Android audio compatibility:
1. WAV desktop audio upload
2. Android WebM/Opus audio upload and transparent conversion
3. Extensionless WebM upload (magic bytes detection)
4. Invalid/corrupted audio handling
5. End-to-end voice-to-ticket pipeline using WebM audio
"""

import sys
import json
import time
import subprocess
from pathlib import Path
import urllib.request
import urllib.error

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    symbol = "✔" if status == "PASS" else "✖" if status == "FAIL" else "ℹ"
    print(f"[{symbol}] {msg}")

def upload_multipart_audio(audio_path: Path, filename: str, content_type: str):
    url = f"{BASE_URL}/api/transcribe"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    audio_bytes = audio_path.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="audio_file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + audio_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=45) as res:
        status_code = res.status
        data = json.loads(res.read().decode('utf-8'))
        return status_code, data

def request_json(method, path, data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode('utf-8') if data else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as res:
        return res.status, json.loads(res.read().decode('utf-8'))

def main():
    print("=" * 70)
    print("  BOLTI SLIP — ANDROID AUDIO COMPATIBILITY & REGRESSION SUITE")
    print("=" * 70)

    # 1. Start FastAPI server
    py_exe = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    log("Starting FastAPI uvicorn server on port 8000...")
    proc = subprocess.Popen(
        [str(py_exe), "-m", "uvicorn", "backend.main:app", "--port", "8000"],
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server ready
    ready = False
    for attempt in range(1, 15):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2) as res:
                if res.status == 200:
                    ready = True
                    log(f"Server ready after {attempt}s!", "PASS")
                    break
        except Exception:
            time.sleep(1)

    if not ready:
        log("Server failed to respond on /api/health!", "FAIL")
        proc.kill()
        return

    wav_src = ROOT_DIR / "test_audio.wav"
    webm_src = ROOT_DIR / "test_android_recorded.webm"
    webm_no_ext = ROOT_DIR / "test_android_blob_no_ext"
    invalid_file = ROOT_DIR / "test_invalid.wav"

    try:
        # Create WebM test audio from WAV using FFmpeg with Opus codec (matching Android MediaRecorder)
        log("Synthesizing Android WebM/Opus audio with FFmpeg...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav_src), "-c:a", "libopus", str(webm_src)],
            capture_output=True,
            check=True
        )
        # Create extensionless copy to test magic-byte detection
        webm_no_ext.write_bytes(webm_src.read_bytes())
        # Create corrupted audio
        invalid_file.write_text("This is not valid audio data.", encoding="utf-8")

        # -------------------------------------------------------------
        # TEST 1: Existing Desktop WAV Upload
        # -------------------------------------------------------------
        print("\n--- TEST 1: Existing Desktop WAV Upload ---")
        st, res = upload_multipart_audio(wav_src, "test_audio.wav", "audio/wav")
        assert st == 200 and res.get("success") is True, f"WAV upload failed: {res}"
        assert "mixer grinder" in res.get("transcript", "").lower()
        log(f"WAV transcription PASSED: \"{res.get('transcript')}\"", "PASS")

        # -------------------------------------------------------------
        # TEST 2: Android WebM/Opus Upload (Auto-Converted to WAV)
        # -------------------------------------------------------------
        print("\n--- TEST 2: Android WebM/Opus Upload & Auto-Conversion ---")
        st, res_webm = upload_multipart_audio(webm_src, "recording.webm", "audio/webm;codecs=opus")
        assert st == 200 and res_webm.get("success") is True, f"WebM upload failed: {res_webm}"
        assert "mixer grinder" in res_webm.get("transcript", "").lower()
        log(f"Android WebM/Opus transcription PASSED: \"{res_webm.get('transcript')}\"", "PASS")

        # -------------------------------------------------------------
        # TEST 3: WebM Upload without Extension (Magic Bytes EBML Check)
        # -------------------------------------------------------------
        print("\n--- TEST 3: Extensionless WebM Upload (Magic Bytes) ---")
        st, res_magic = upload_multipart_audio(webm_no_ext, "blob", "audio/webm")
        assert st == 200 and res_magic.get("success") is True, f"Magic bytes test failed: {res_magic}"
        assert "mixer grinder" in res_magic.get("transcript", "").lower()
        log(f"Extensionless WebM transcription PASSED: \"{res_magic.get('transcript')}\"", "PASS")

        # -------------------------------------------------------------
        # TEST 4: Invalid / Corrupted Audio Handling
        # -------------------------------------------------------------
        print("\n--- TEST 4: Invalid / Corrupted Audio Handling ---")
        st, res_invalid = upload_multipart_audio(invalid_file, "corrupt.wav", "audio/wav")
        # Should gracefully fail with success=False, without crashing FastAPI
        assert st == 200 and res_invalid.get("success") is False
        log(f"Gracefully rejected invalid audio: Error={res_invalid.get('error')}", "PASS")

        # -------------------------------------------------------------
        # TEST 5: Complete Voice-to-Ticket Pipeline from WebM Audio
        # -------------------------------------------------------------
        print("\n--- TEST 5: Complete Voice-to-Ticket Pipeline from WebM ---")
        transcript = res_webm.get("transcript")
        log(f"Extracting fields from WebM transcript: \"{transcript}\"")
        st, ext_res = request_json("POST", "/api/extract", {"transcript": transcript})
        assert st == 200 and ext_res.get("success") is True
        f = ext_res["fields"]
        log(f"Extracted: Device={f.get('device_description')}, Delivery={f.get('expected_delivery')}", "PASS")

        # Create ticket in SQLite
        ticket_payload = {
            "device_description": f.get("device_description") or "Mixer Grinder",
            "reported_problem": f.get("reported_problem") or "Kharab ho gaya hai",
            "expected_delivery": f.get("expected_delivery") or "2026-11-13",
            "estimated_cost": 350.0,
            "transcript_raw": transcript
        }
        st, created_ticket = request_json("POST", "/api/tickets", ticket_payload)
        assert st == 201
        t_id = created_ticket["id"]
        t_num = created_ticket["ticket_number"]
        log(f"Created ticket #{t_id} ({t_num}) from WebM speech", "PASS")

        # Confirm via Timbre TTS
        req_confirm = urllib.request.Request(f"{BASE_URL}/api/tickets/{t_id}/confirm", method="POST")
        with urllib.request.urlopen(req_confirm, timeout=30) as confirm_res:
            assert confirm_res.status == 200
            audio_bytes = confirm_res.read()
            assert audio_bytes[:4] == b"RIFF" and len(audio_bytes) > 1000
            log(f"Timbre TTS spoken confirmation generated: {len(audio_bytes)} bytes WAV", "PASS")

        print("\n" + "=" * 70)
        print("  ALL ANDROID AUDIO COMPATIBILITY TESTS PASSED (100%)")
        print("=" * 70)

    finally:
        # Cleanup temp test files
        webm_src.unlink(missing_ok=True)
        webm_no_ext.unlink(missing_ok=True)
        invalid_file.unlink(missing_ok=True)

        log("Shutting down uvicorn test process...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log("Server stopped.")

if __name__ == "__main__":
    main()
