"""
scripts/test_batch1_security.py
--------------------------------
Comprehensive automated test suite for Batch 1: Authentication and API Security.
Tests:
  1. Backend import and route verification
  2. Rate limiting on POST /api/auth/login (10/min, 429 response)
  3. Speech API protection (transcribe, speak, confirm require auth)
  4. Password change and other-session revocation
  5. Seed password removal verification and DB preservation
"""

import atexit
import gc
import io
import os
import sqlite3
import sys
import tempfile
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# ---------------------------------------------------------------------------
# TEST DATABASE ISOLATION
# ---------------------------------------------------------------------------
# Monkeypatch _DB_PATH BEFORE importing app so that:
#   - sync_init_db() initializes a temp DB (not bolti_slip.db)
#   - get_db() serves connections to the temp DB
#   - create_backup() reads the temp DB path
# Suite 5 still reads the REAL bolti_slip.db directly for preservation checks.
# ---------------------------------------------------------------------------
_TEMP_DIR = tempfile.mkdtemp(prefix="bolti_test_b1_")
_TEMP_DB_PATH = Path(_TEMP_DIR) / "test_batch1.db"

import backend.database.db as _db_mod

_ORIGINAL_DB_PATH = _db_mod._DB_PATH
_db_mod._DB_PATH = _TEMP_DB_PATH

# Safety assertion: confirm isolation is active
assert _db_mod._DB_PATH.resolve() != (PROJECT_ROOT / "bolti_slip.db").resolve(), \
    "SAFETY: Tests must not use live database!"

# Explicitly initialize the isolated temporary database schema
_db_mod.sync_init_db()

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.limiter import limiter


def _cleanup_test_db():
    """Restore original _DB_PATH and remove temp files."""
    _db_mod._DB_PATH = _ORIGINAL_DB_PATH
    gc.collect()
    try:
        if _TEMP_DB_PATH.exists():
            _TEMP_DB_PATH.unlink(missing_ok=True)
        # Clean WAL/SHM if present
        for suffix in (".db-wal", ".db-shm"):
            p = _TEMP_DB_PATH.with_suffix(suffix)
            if p.exists():
                p.unlink(missing_ok=True)
        Path(_TEMP_DIR).rmdir()
    except Exception:
        pass  # Windows file locks; temp dir will be cleaned by OS

atexit.register(_cleanup_test_db)

PASS = 0
FAIL = 0
results = []


def ok(name):
    global PASS
    PASS += 1
    results.append(("PASS", name))
    print(f"  [PASS] {name}", flush=True)


def fail(name, reason=""):
    global FAIL
    FAIL += 1
    tag = f"  [FAIL] {name}"
    if reason:
        tag += f" -- {reason}"
    results.append(("FAIL", name, reason))
    print(tag, flush=True)


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}", flush=True)


client = TestClient(app)


# ---------------------------------------------------------------------------
# TEST SUITE 1: Backend Import & Route Registration
# ---------------------------------------------------------------------------
section("1. BACKEND IMPORT & ROUTE REGISTRATION")

try:
    assert app is not None
    ok("FastAPI app instance initialized")
except Exception as e:
    fail("FastAPI app instance initialized", str(e))

try:
    assert hasattr(app.state, "limiter")
    assert app.state.limiter is limiter
    ok("Rate limiter attached to app.state.limiter")
except Exception as e:
    fail("Rate limiter attached to app.state.limiter", str(e))

expected_routes = [
    ("/api/auth/login", "POST"),
    ("/api/auth/register", "POST"),
    ("/api/auth/me", "GET"),
    ("/api/auth/change-password", "POST"),
    ("/api/transcribe", "POST"),
    ("/api/speak", "POST"),
    ("/api/tickets/{ticket_id}/confirm", "POST"),
    ("/api/health", "GET"),
]

registered_routes = {
    (route.path, method)
    for route in app.routes
    for method in (route.methods or set())
}

for path, method in expected_routes:
    if (path, method) in registered_routes:
        ok(f"Route {method} {path} registered")
    else:
        fail(f"Route {method} {path} registered", "Not found in app.routes")


# ---------------------------------------------------------------------------
# TEST SUITE 2: Speech API Endpoints Authentication (TASK 2)
# ---------------------------------------------------------------------------
section("2. SPEECH API ENDPOINTS AUTHENTICATION")

# 2.1 /api/transcribe without token -> 401
dummy_wav = b"RIFF....WAVEfmt ...."
files = {"audio_file": ("test.wav", io.BytesIO(dummy_wav), "audio/wav")}
res = client.post("/api/transcribe", files=files)
if res.status_code == 401:
    ok("POST /api/transcribe without token returns 401 Unauthorized")
else:
    fail("POST /api/transcribe without token returns 401", f"Got status {res.status_code}: {res.text}")

# 2.2 /api/transcribe with invalid token -> 401
res = client.post("/api/transcribe", files={"audio_file": ("test.wav", io.BytesIO(dummy_wav), "audio/wav")}, headers={"Authorization": "Bearer bad-token-12345"})
if res.status_code == 401:
    ok("POST /api/transcribe with invalid token returns 401 Unauthorized")
else:
    fail("POST /api/transcribe with invalid token returns 401", f"Got status {res.status_code}: {res.text}")

# 2.3 /api/speak without token -> 401
res = client.post("/api/speak", json={"text": "Test audio", "voice": "Devansh", "language": "hi-IN"})
if res.status_code == 401:
    ok("POST /api/speak without token returns 401 Unauthorized")
else:
    fail("POST /api/speak without token returns 401", f"Got status {res.status_code}: {res.text}")

# 2.4 /api/speak with invalid token -> 401
res = client.post("/api/speak", json={"text": "Test audio"}, headers={"Authorization": "Bearer bad-token-12345"})
if res.status_code == 401:
    ok("POST /api/speak with invalid token returns 401 Unauthorized")
else:
    fail("POST /api/speak with invalid token returns 401", f"Got status {res.status_code}: {res.text}")

# 2.5 /api/tickets/{id}/confirm without token -> 401
res = client.post("/api/tickets/1/confirm")
if res.status_code == 401:
    ok("POST /api/tickets/1/confirm without token returns 401 Unauthorized")
else:
    fail("POST /api/tickets/1/confirm without token returns 401", f"Got status {res.status_code}: {res.text}")


# ---------------------------------------------------------------------------
# TEST SUITE 3: Password Change & Session Revocation (TASK 3)
# ---------------------------------------------------------------------------
section("3. PASSWORD CHANGE & SESSION REVOCATION")

# Register a unique test shopkeeper for this test run
test_user = f"tuser_{uuid.uuid4().hex[:8]}"
initial_pw = "InitSecret@123"
new_pw = "NewSecret@456"

reg_res = client.post("/api/auth/register", json={
    "username": test_user,
    "password": initial_pw,
    "shop_name": "Test Shop Revocation",
    "owner_name": "Test Owner",
    "phone": "9998887776",
})

if reg_res.status_code == 201:
    token_1 = reg_res.json()["token"]
    ok("Registered test shopkeeper successfully")
else:
    fail("Registered test shopkeeper successfully", f"{reg_res.status_code}: {reg_res.text}")
    token_1 = None

if token_1:
    # Create a second active session for the same shop
    login2_res = client.post("/api/auth/login", json={"username": test_user, "password": initial_pw})
    if login2_res.status_code == 200:
        token_2 = login2_res.json()["token"]
        ok("Created second active session (token_2)")
    else:
        fail("Created second active session (token_2)", f"{login2_res.status_code}: {login2_res.text}")
        token_2 = None

    # Verify both tokens can access /api/auth/me
    me_1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_1}"})
    me_2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_2}"})
    if me_1.status_code == 200 and me_2.status_code == 200:
        ok("Both active session tokens authenticated on /api/auth/me")
    else:
        fail("Both active session tokens authenticated", f"token_1: {me_1.status_code}, token_2: {me_2.status_code}")

    # Test wrong current password rejected
    bad_pw_res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"current_password": "WrongPassword!999", "new_password": new_pw},
    )
    if bad_pw_res.status_code == 400:
        ok("Incorrect current password returns HTTP 400 Bad Request")
    else:
        fail("Incorrect current password returns HTTP 400", f"Got status {bad_pw_res.status_code}: {bad_pw_res.text}")

    # Change password with valid credentials using token_1
    change_res = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"current_password": initial_pw, "new_password": new_pw},
    )
    if change_res.status_code == 200 and change_res.json().get("success"):
        ok("Password changed successfully using token_1")
    else:
        fail("Password changed successfully", f"Got status {change_res.status_code}: {change_res.text}")

    # Verify token_1 (current session) is PRESERVED and still works
    me_1_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_1}"})
    if me_1_after.status_code == 200:
        ok("Current session (token_1) preserved and remains active")
    else:
        fail("Current session (token_1) preserved", f"Got status {me_1_after.status_code}: {me_1_after.text}")

    # Verify token_2 (other session) is REVOKED
    me_2_after = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_2}"})
    if me_2_after.status_code == 401:
        ok("Other session (token_2) successfully revoked (returns 401)")
    else:
        fail("Other session (token_2) revoked", f"Expected 401, got {me_2_after.status_code}: {me_2_after.text}")

    # Verify old password cannot log in
    old_login_res = client.post("/api/auth/login", json={"username": test_user, "password": initial_pw})
    if old_login_res.status_code == 401:
        ok("Old password rejected on login (returns 401)")
    else:
        fail("Old password rejected on login", f"Expected 401, got {old_login_res.status_code}")

    # Verify new password CAN log in
    new_login_res = client.post("/api/auth/login", json={"username": test_user, "password": new_pw})
    if new_login_res.status_code == 200:
        token_3 = new_login_res.json()["token"]
        ok("New password successfully logs in (returns 200 and new token)")
    else:
        fail("New password logs in", f"Got status {new_login_res.status_code}: {new_login_res.text}")

    # Verify authenticated speech endpoints work with the valid token
    # (Testing that auth dependency accepts valid token; service error or 200 is acceptable, NOT 401)
    spk_auth_res = client.post(
        "/api/speak",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"text": "Namaste", "voice": "Devansh", "language": "hi-IN"},
    )
    if spk_auth_res.status_code != 401:
        ok(f"Authenticated /api/speak passed auth layer (HTTP {spk_auth_res.status_code}, not 401)")
    else:
        fail("Authenticated /api/speak passed auth layer", "Returned 401 with valid token")


# ---------------------------------------------------------------------------
# TEST SUITE 4: Rate Limiting on POST /api/auth/login (TASK 1)
# ---------------------------------------------------------------------------
section("4. LOGIN RATE LIMITING (10/min per IP)")

# Reset limiter storage for this test to ensure clean count
limiter.reset()

login_status_codes = []
for i in range(12):
    # Attempt login with random credentials
    r = client.post(
        "/api/auth/login",
        json={"username": "random_rate_user", "password": "WrongPassword123!"},
    )
    login_status_codes.append(r.status_code)

first_10_codes = login_status_codes[:10]
rate_limited_codes = login_status_codes[10:]

# First 10 should be 401 Unauthorized (normal response for invalid credentials)
if all(code == 401 for code in first_10_codes):
    ok("First 10 login attempts processed normally (HTTP 401)")
else:
    fail("First 10 login attempts processed normally", f"Got codes: {first_10_codes}")

# 11th and 12th should be 429 Too Many Requests
if login_status_codes[10] == 429:
    ok("11th login attempt within 1 minute returns HTTP 429 Too Many Requests")
else:
    fail("11th login attempt returns HTTP 429", f"Got status {login_status_codes[10]}")

# Check 429 error message format
r_429 = client.post(
    "/api/auth/login",
    json={"username": "random_rate_user", "password": "WrongPassword123!"},
)
detail = r_429.json().get("detail", "")
if r_429.status_code == 429 and "Too many requests" in detail:
    ok(f"HTTP 429 response body contains generic error: '{detail}'")
else:
    fail("HTTP 429 response body contains generic error", f"Got body: {r_429.text}")

# Ensure rate limiting on login does not block /api/auth/register
rand_reg_user = f"reg_user_{uuid.uuid4().hex[:6]}"
reg_res = client.post("/api/auth/register", json={
    "username": rand_reg_user,
    "password": "ValidPassword@123",
    "shop_name": "Non-blocked Shop",
    "owner_name": "Test",
})
if reg_res.status_code == 201:
    ok("Registration (/api/auth/register) is NOT blocked while login is rate-limited")
else:
    fail("Registration not blocked while login rate-limited", f"Got status {reg_res.status_code}")

# Reset limiter after test
limiter.reset()


# ---------------------------------------------------------------------------
# TEST SUITE 5: Seed Password Removal & Database Preservation (TASK 4)
# ---------------------------------------------------------------------------
section("5. SEED PASSWORD REMOVAL & DATABASE PRESERVATION")

db_py_path = PROJECT_ROOT / "backend" / "database" / "db.py"
db_py_content = db_py_path.read_text(encoding="utf-8")

if "Sharma@123" not in db_py_content:
    ok("Hardcoded seed password 'Sharma@123' removed from backend/database/db.py")
else:
    fail("Hardcoded seed password removed from backend/database/db.py", "Found 'Sharma@123' in db.py")

if "os.getenv(\"BOLTI_SEED_PASSWORD\")" in db_py_content or "os.getenv('BOLTI_SEED_PASSWORD')" in db_py_content:
    ok("Environment variable BOLTI_SEED_PASSWORD used in db.py for seed fallback")
else:
    fail("BOLTI_SEED_PASSWORD used in db.py", "Pattern not found")

# Verify SQLite database data preservation
conn = sqlite3.connect(PROJECT_ROOT / "bolti_slip.db")
c = conn.cursor()

# Check Sharma account exists
sharma_shop = c.execute("SELECT id, username, shop_name FROM shops WHERE id = 1").fetchone()
if sharma_shop and sharma_shop[1] == "sharma":
    ok("Original shop record (id=1, username=sharma) preserved")
else:
    fail("Original shop record preserved", f"Got {sharma_shop}")

# Check all 8 original tickets BLT-0001 through BLT-0008
ticket_count = c.execute("SELECT count(*) FROM tickets WHERE shop_id = 1").fetchone()[0]
if ticket_count >= 8:
    ok(f"Original tickets preserved (shop_id=1 has {ticket_count} tickets >= 8)")
else:
    fail("Original tickets preserved", f"Only {ticket_count} tickets found for shop_id=1")

conn.close()


# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
section("SUMMARY")
print(f"\n  Total Tests: {PASS + FAIL} | PASSED: {PASS} | FAILED: {FAIL}\n", flush=True)
if FAIL == 0:
    print("  *** ALL BATCH 1 TESTS PASSED ***", flush=True)
else:
    print("  *** SOME TESTS FAILED ***", flush=True)
    for status, name, *rest in results:
        if status == "FAIL":
            print(f"    FAIL: {name} {rest[0] if rest else ''}", flush=True)

sys.exit(0 if FAIL == 0 else 1)
