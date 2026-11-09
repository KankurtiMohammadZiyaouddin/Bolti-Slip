# Bolti Slip — Batch 1: Authentication and API Security Report

**Date:** 2026-11-09  
**Milestone:** Security Fixes — Batch 1  
**Project:** `C:\Programs\Project\Bolti-Slip`  
**Status:** ALL TESTS PASSED (33/33 backend tests + TypeScript compilation + Vite production build)

---

## 1. Executive Summary

Batch 1 addressed four key security findings identified during the security audit:
1. **Login Brute-Force Rate Limiting:** Added IP-based rate limiting on `POST /api/auth/login` (10 requests/minute per IP) using `slowapi`, returning HTTP 429 with generic error responses without impacting registration or legitimate traffic.
2. **Speech API Protection:** Added the `get_current_shop` authentication dependency to `POST /api/transcribe` and `POST /api/speak`, preventing unauthenticated access or quota exhaustion.
3. **Password Change Session Revocation:** Enhanced `POST /api/auth/change-password` to revoke all other active sessions for the shopkeeper while safely preserving the current session, preventing session persistence across compromise.
4. **Hardcoded Seed Password Removal:** Replaced the hardcoded `"Sharma@123"` seed initializer in `backend/database/db.py` with an environment variable (`BOLTI_SEED_PASSWORD`) and cryptographic random fallback (`secrets.token_urlsafe(16)`). Existing database records, shops, and tickets were fully preserved.

---

## 2. Files Modified

| File | Type | Changes |
|------|------|---------|
| `backend/services/limiter.py` | New file | Centralized `slowapi.Limiter` instance keyed by client IP (`get_remote_address`). |
| `backend/main.py` | Modified | Attached `app.state.limiter` and custom `RateLimitExceeded` handler returning HTTP 429 with standard `{"detail": "Too many requests. Please try again later."}` response. |
| `backend/routers/auth.py` | Modified | Added `@limiter.limit("10/minute")` and `Request` parameter to `POST /api/auth/login`. Updated `change_password` to revoke other active sessions via `revoke_other_sessions(db, shop_id, keep_token=current_token)`. |
| `backend/services/auth.py` | Modified | Added `revoke_other_sessions(db, shop_id, keep_token)` helper to safely delete all other active sessions while preserving the calling token. |
| `backend/routers/transcription.py` | Modified | Added `current_shop: dict = Depends(get_current_shop)` to `POST /api/transcribe`. |
| `backend/routers/speech.py` | Modified | Added `current_shop: dict = Depends(get_current_shop)` to `POST /api/speak`. |
| `backend/database/db.py` | Modified | Removed `"Sharma@123"`. Now uses `os.getenv("BOLTI_SEED_PASSWORD")` or `secrets.token_urlsafe(16)`. Existing shops are untouched. |
| `.env.example` | Modified | Added documented templates for `GNANI_API_KEY_ID` and `BOLTI_SEED_PASSWORD`. |
| `backend/requirements.txt` | Modified | Added `slowapi>=0.1.10`. |
| `scripts/test_batch1_security.py` | New test file | 33 automated tests validating rate limiting, speech auth, password change session revocation, and DB preservation. |

---

## 3. Exact Code Changes

### 3.1 Rate Limiting Service (`backend/services/limiter.py`)
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
```

### 3.2 FastAPI App Configuration (`backend/main.py`)
```python
from slowapi.errors import RateLimitExceeded
from backend.services.limiter import limiter

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )
```

### 3.3 Login Route Protection (`backend/routers/auth.py`)
```python
@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: ShopLogin, db: aiosqlite.Connection = Depends(get_db)):
    ...
```

### 3.4 Speech Endpoint Protection (`backend/routers/transcription.py` & `backend/routers/speech.py`)
```python
# transcription.py
@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    current_shop: dict = Depends(get_current_shop),
):
    ...

# speech.py
@router.post("/speak")
async def speak(
    body: SpeakRequest,
    current_shop: dict = Depends(get_current_shop),
):
    ...
```

### 3.5 Password Change Session Revocation (`backend/routers/auth.py` & `backend/services/auth.py`)
```python
# services/auth.py
async def revoke_other_sessions(db: aiosqlite.Connection, shop_id: int, keep_token: Optional[str] = None) -> int:
    """Revoke all sessions for a shop, optionally preserving keep_token."""
    if keep_token:
        cursor = await db.execute(
            "DELETE FROM sessions WHERE shop_id = ? AND token != ?",
            (shop_id, keep_token),
        )
    else:
        cursor = await db.execute(
            "DELETE FROM sessions WHERE shop_id = ?",
            (shop_id,),
        )
    await db.commit()
    return cursor.rowcount

# routers/auth.py
@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    shop_id = current_shop["id"]
    cursor = await db.execute("SELECT password_hash FROM shops WHERE id = ?", (shop_id,))
    row = await cursor.fetchone()
    if not row or not verify_password(body.current_password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            current_token = parts[1]

    new_hash = hash_password(body.new_password)
    await db.execute("UPDATE shops SET password_hash = ? WHERE id = ?", (new_hash, shop_id))
    await revoke_other_sessions(db, shop_id, keep_token=current_token)
    await db.commit()
    return {"success": True, "message": "Password changed successfully."}
```

### 3.6 Seed Password Removal (`backend/database/db.py`)
```python
        # Seed default shopkeeper (Sharma Electronics) if no shops exist
        cursor.execute("SELECT COUNT(*) FROM shops")
        shop_count = cursor.fetchone()[0]
        if shop_count == 0:
            import os
            import secrets
            from backend.services.auth import hash_password

            seed_password = os.getenv("BOLTI_SEED_PASSWORD")
            if not seed_password:
                seed_password = secrets.token_urlsafe(16)

            default_hash = hash_password(seed_password)
            conn.execute(
                """
                INSERT INTO shops (id, username, password_hash, shop_name, owner_name, phone, branch, address)
                VALUES (1, 'sharma', ?, 'Sharma Electronics', 'Rajesh Sharma', '9876543210', 'Pune Main Branch', 'Shop 4, Market Yard, Pune')
                """,
                (default_hash,)
            )
            conn.commit()
```

---

## 4. Tests Actually Executed

Test Suite: `scripts/test_batch1_security.py`  
Command: `.venv\Scripts\python.exe scripts\test_batch1_security.py`

### Test Results Breakdown (33 Tests)

#### Section 1: Backend Import & Route Registration
| # | Test Assertion | Result |
|---|----------------|--------|
| 1 | FastAPI app instance initialized | ✅ PASS |
| 2 | Rate limiter attached to app.state.limiter | ✅ PASS |
| 3 | Route POST `/api/auth/login` registered | ✅ PASS |
| 4 | Route POST `/api/auth/register` registered | ✅ PASS |
| 5 | Route GET `/api/auth/me` registered | ✅ PASS |
| 6 | Route POST `/api/auth/change-password` registered | ✅ PASS |
| 7 | Route POST `/api/transcribe` registered | ✅ PASS |
| 8 | Route POST `/api/speak` registered | ✅ PASS |
| 9 | Route POST `/api/tickets/{ticket_id}/confirm` registered | ✅ PASS |
| 10 | Route GET `/api/health` registered | ✅ PASS |

#### Section 2: Speech API Endpoints Authentication (TASK 2)
| # | Test Assertion | Result |
|---|----------------|--------|
| 11 | POST `/api/transcribe` without token returns 401 Unauthorized | ✅ PASS |
| 12 | POST `/api/transcribe` with invalid token returns 401 Unauthorized | ✅ PASS |
| 13 | POST `/api/speak` without token returns 401 Unauthorized | ✅ PASS |
| 14 | POST `/api/speak` with invalid token returns 401 Unauthorized | ✅ PASS |
| 15 | POST `/api/tickets/1/confirm` without token returns 401 Unauthorized | ✅ PASS |

#### Section 3: Password Change & Session Revocation (TASK 3)
| # | Test Assertion | Result |
|---|----------------|--------|
| 16 | Registered test shopkeeper successfully | ✅ PASS |
| 17 | Created second active session (`token_2`) | ✅ PASS |
| 18 | Both active session tokens authenticated on `/api/auth/me` | ✅ PASS |
| 19 | Incorrect current password returns HTTP 400 Bad Request | ✅ PASS |
| 20 | Password changed successfully using `token_1` | ✅ PASS |
| 21 | Current session (`token_1`) preserved and remains active | ✅ PASS |
| 22 | Other session (`token_2`) successfully revoked (returns HTTP 401) | ✅ PASS |
| 23 | Old password rejected on login (returns HTTP 401) | ✅ PASS |
| 24 | New password successfully logs in (returns HTTP 200 and new token) | ✅ PASS |
| 25 | Authenticated `/api/speak` passes auth layer with valid token | ✅ PASS |

#### Section 4: Login Rate Limiting (TASK 1)
| # | Test Assertion | Result |
|---|----------------|--------|
| 26 | First 10 login attempts processed normally (HTTP 401 for bad creds) | ✅ PASS |
| 27 | 11th login attempt within 1 minute returns HTTP 429 Too Many Requests | ✅ PASS |
| 28 | HTTP 429 response contains generic error message | ✅ PASS |
| 29 | Registration (`/api/auth/register`) is NOT blocked while login is rate-limited | ✅ PASS |

#### Section 5: Seed Password Removal & Database Preservation (TASK 4)
| # | Test Assertion | Result |
|---|----------------|--------|
| 30 | Hardcoded seed password removed from `backend/database/db.py` | ✅ PASS |
| 31 | Environment variable `BOLTI_SEED_PASSWORD` used in `db.py` | ✅ PASS |
| 32 | Original shop record (`id=1`, `username=sharma`) preserved in database | ✅ PASS |
| 33 | All original tickets preserved (shop_id=1 has 8 tickets >= 8) | ✅ PASS |

---

## 5. Frontend TypeScript Compilation & Production Build

Command: `npm --prefix frontend run build`

```
> bolti-slip-frontend@1.0.0 build
> tsc -b && vite build

vite v5.4.21 building for production...
transforming...
✓ 63 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                    1.98 kB │ gzip:  0.88 kB
dist/assets/index-CdWofOve.css                    41.18 kB │ gzip:  8.11 kB
dist/assets/workbox-window.prod.es5-BqEJf4Xk.js    5.71 kB │ gzip:  2.34 kB
dist/assets/index-DPdU0Lzn.js                    280.75 kB │ gzip: 78.12 kB
✓ built in 4.39s

PWA v2.0.0
mode      generateSW
precache  14 entries (345.23 KiB)
files generated
  dist/sw.js
  dist/workbox-796b0218.js
```
**Status: ✅ SUCCESS (Exit code 0, 0 errors, PWA service worker generated).**

---

## 6. Frontend API Wrapper Verification

Checked `frontend/src/api/client.ts`:
- `transcribeAudio(audioBlob, filename)`: Uses `headers: getHeaders()` -> automatically attaches `Authorization: Bearer <token>`.
- `speakText(text, voice, language)`: Uses `headers: getHeaders({ 'Content-Type': 'application/json' })` -> automatically attaches `Authorization: Bearer <token>`.
- `confirmTicket(id)`: Uses `headers: getHeaders()` -> automatically attaches `Authorization: Bearer <token>`.
- `changePassword(current_password, new_password)`: Uses `headers: getHeaders(...)` -> automatically attaches `Authorization: Bearer <token>`.

No frontend code changes were needed; all wrappers already send authentication headers.

---

## 7. Remaining Risks & Recommendations (Post-Batch 1)

1. **CORS Allow Origins:**
   `backend/main.py` currently permits localhost origins. When deploying behind Cloudflare Tunnel or a production domain, the production host should be added to `allow_origins`.
2. **Database Backups:**
   Automated SQLite snapshotting/backup (`sqlite3 .backup`) is recommended prior to live multi-tenant production use.
3. **Audio File Size Validation:**
   Adding an explicit payload size limit (e.g. 25 MB) on `POST /api/transcribe` will prevent client-side upload denial-of-service.
