"""
tests/verify_functional_milestone2.py
-------------------------------------
End-to-end functional verification script for Bolti Slip Milestone 2.
Tests all backend routes, database CRUD, extraction, transcription, and TTS.
"""

import sys
import time
import json
import subprocess
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

import urllib.request
import urllib.error

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[TEST] {msg}")

def request_json(method, path, data=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode('utf-8') if data else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as res:
        status = res.status
        resp_data = json.loads(res.read().decode('utf-8'))
        return status, resp_data

def request_raw(method, path, data=None, content_type="application/json"):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": content_type} if content_type else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as res:
        status = res.status
        resp_bytes = res.read()
        resp_headers = dict(res.headers)
        return status, resp_bytes, resp_headers

def test_multipart_transcribe():
    url = f"{BASE_URL}/api/transcribe"
    audio_path = ROOT_DIR / "test_audio.wav"
    if not audio_path.exists():
        log(f"WARNING: {audio_path} not found")
        return False, "test_audio.wav missing"

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    audio_bytes = audio_path.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="audio_file"; filename="test_audio.wav"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode("utf-8") + audio_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        status = res.status
        data = json.loads(res.read().decode('utf-8'))
        return status == 200, data

def main():
    print("=" * 70)
    print("  BOLTI SLIP — MILESTONE 2 FUNCTIONAL VERIFICATION SUITE")
    print("=" * 70)

    # 1. Start FastAPI server
    log("Starting FastAPI uvicorn server on port 8000...")
    py_exe = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    proc = subprocess.Popen(
        [str(py_exe), "-m", "uvicorn", "backend.main:app", "--port", "8000"],
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    results = {}
    
    # Wait for server to become responsive
    log("Waiting for uvicorn to become ready...")
    ready = False
    for attempt in range(1, 15):
        try:
            with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2) as res:
                if res.status == 200:
                    ready = True
                    log(f"Server ready after {attempt}s!")
                    break
        except Exception:
            time.sleep(1)

    if not ready:
        log("Server failed to respond on /api/health!")
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=5)
            print("Uvicorn stderr:", stderr.decode('utf-8', errors='ignore'))
            print("Uvicorn stdout:", stdout.decode('utf-8', errors='ignore'))
        except Exception as e:
            proc.kill()
            print("Could not get proc output:", e)
        return

    try:
        # Test 1: GET /api/health
        log("Testing GET /api/health...")
        st, data = request_json("GET", "/api/health")
        assert st == 200 and data.get("status") == "ok"
        results["health_check"] = {"status": "PASSED", "data": data}
        log(f"  --> PASSED: {data}")

        # Test 2: GET /api/tickets (Dashboard stats & history)
        log("Testing GET /api/tickets...")
        st, tickets = request_json("GET", "/api/tickets")
        assert st == 200 and isinstance(tickets, list)
        total = len(tickets)
        pending = sum(1 for t in tickets if t["status"] == "open")
        in_prog = sum(1 for t in tickets if t["status"] == "in_progress")
        comp = sum(1 for t in tickets if t["status"] in ("resolved", "closed"))
        results["list_tickets"] = {
            "status": "PASSED",
            "count": total,
            "pending": pending,
            "in_progress": in_prog,
            "completed": comp
        }
        log(f"  --> PASSED: Total: {total}, Pending: {pending}, In Progress: {in_prog}, Completed: {comp}")

        # Test 3: POST /api/extract
        log("Testing POST /api/extract...")
        extract_req = {
            "transcript": "Bhai mera Philips steam iron kharab hai, heating nahi ho rahi hai, kal tak theek kar dena, 350 rupaye."
        }
        st, ext_res = request_json("POST", "/api/extract", extract_req)
        assert st == 200 and ext_res["success"] is True
        f = ext_res["fields"]
        assert "Iron" in f["device_description"]
        assert f["estimated_cost"] == 350.0
        results["extract_api"] = {
            "status": "PASSED",
            "device": f["device_description"],
            "cost": f["estimated_cost"],
            "delivery": f["expected_delivery"],
            "missing_fields": ext_res["missing_fields"]
        }
        log(f"  --> PASSED: Device={f['device_description']}, Cost={f['estimated_cost']}, Missing={ext_res['missing_fields']}")

        # Test 4: POST /api/tickets (Create Ticket)
        log("Testing POST /api/tickets (Create Ticket)...")
        create_payload = {
            "customer_name": "Test Customer Ziya",
            "customer_phone": "9876543210",
            "device_description": "Philips Steam Iron",
            "reported_problem": "Heating element damaged",
            "repair_instructions": "Replace thermal fuse",
            "expected_delivery": "2026-11-08",
            "estimated_cost": 350.0,
            "transcript_raw": extract_req["transcript"]
        }
        st, new_ticket = request_json("POST", "/api/tickets", create_payload)
        assert st == 201
        new_id = new_ticket["id"]
        ticket_number = new_ticket["ticket_number"]
        results["create_ticket"] = {"status": "PASSED", "id": new_id, "ticket_number": ticket_number}
        log(f"  --> PASSED: Created Ticket #{new_id} ({ticket_number})")

        # Test 5: GET /api/tickets/{id}
        log(f"Testing GET /api/tickets/{new_id}...")
        st, fetched = request_json("GET", f"/api/tickets/{new_id}")
        assert st == 200 and fetched["ticket_number"] == ticket_number
        results["get_ticket"] = {"status": "PASSED", "ticket_number": ticket_number}
        log(f"  --> PASSED: Fetched ticket #{new_id}")

        # Test 6: PATCH /api/tickets/{id}/status
        log(f"Testing PATCH /api/tickets/{new_id}/status...")
        st, updated = request_json("PATCH", f"/api/tickets/{new_id}/status", {"status": "in_progress"})
        assert st == 200 and updated["status"] == "in_progress"
        results["update_status"] = {"status": "PASSED", "new_status": updated["status"]}
        log(f"  --> PASSED: Status updated to 'in_progress'")

        # Test 7: POST /api/transcribe (Gnani Prisma STT using test_audio.wav)
        log("Testing POST /api/transcribe (Prisma v3.0 STT)...")
        try:
            ok, stt_res = test_multipart_transcribe()
            if ok and stt_res.get("success"):
                results["transcribe"] = {
                    "status": "PASSED",
                    "transcript": stt_res.get("transcript"),
                    "model": stt_res.get("model")
                }
                log(f"  --> PASSED: STT returned: \"{stt_res.get('transcript')}\"")
            else:
                results["transcribe"] = {
                    "status": "FAILED",
                    "error": stt_res.get("error") if isinstance(stt_res, dict) else stt_res
                }
                log(f"  --> FAILED: {stt_res}")
        except Exception as e:
            results["transcribe"] = {"status": "FAILED", "error": str(e)}
            log(f"  --> FAILED: {e}")

        # Test 8: POST /api/speak (Gnani Timbre TTS)
        log("Testing POST /api/speak (Timbre v3.0 TTS)...")
        try:
            speak_data = json.dumps({"text": "नमस्ते, बोलती स्लिप में आपका स्वागत है।", "voice": "Devansh"}).encode('utf-8')
            st, audio_bytes, headers = request_raw("POST", "/api/speak", speak_data)
            is_wav = audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"
            assert st == 200 and is_wav and len(audio_bytes) > 1000
            results["speak"] = {
                "status": "PASSED",
                "content_type": headers.get("content-type"),
                "size_bytes": len(audio_bytes),
                "is_valid_wav": is_wav
            }
            log(f"  --> PASSED: Synthesised {len(audio_bytes)} bytes valid WAV audio")
        except Exception as e:
            results["speak"] = {"status": "FAILED", "error": str(e)}
            log(f"  --> FAILED: {e}")

        # Test 9: POST /api/tickets/{id}/confirm (Timbre Spoken Confirmation for Ticket)
        log(f"Testing POST /api/tickets/{new_id}/confirm...")
        try:
            st, confirm_bytes, headers = request_raw("POST", f"/api/tickets/{new_id}/confirm", None, content_type=None)
            is_wav = confirm_bytes[:4] == b"RIFF" and confirm_bytes[8:12] == b"WAVE"
            assert st == 200 and is_wav and len(confirm_bytes) > 1000
            results["confirm_tts"] = {
                "status": "PASSED",
                "ticket_number": headers.get("x-ticket-number"),
                "size_bytes": len(confirm_bytes),
                "is_valid_wav": is_wav
            }
            log(f"  --> PASSED: Generated spoken confirmation {len(confirm_bytes)} bytes WAV")
        except Exception as e:
            results["confirm_tts"] = {"status": "FAILED", "error": str(e)}
            log(f"  --> FAILED: {e}")

    finally:
        log("Shutting down uvicorn test process...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log("Server stopped.")

    print("\n" + "=" * 70)
    print("  VERIFICATION RESULTS SUMMARY")
    print("=" * 70)
    for test_name, res in results.items():
        print(f"  {test_name:<20}: {res['status']} {res}")

if __name__ == "__main__":
    main()
