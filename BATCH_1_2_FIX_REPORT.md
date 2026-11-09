# BOLTI SLIP — BATCH 1.2 MINIMAL FIX REPORT

**Target:** Implementation of the two minimal corrections identified in `BATCH_1_1_READ_ONLY_REVIEW.md`  
**Workspace:** `C:\Programs\Project\Bolti-Slip`  
**Execution Date:** 2026-11-09  
**Status:** **ALL FIXES IMPLEMENTED & 100% OF TESTS PASSED**

---

## 1. Overview of Fixes Implemented

In accordance with the requirements of Batch 1.2, only the two non-blocking items from the Batch 1.1 read-only review were addressed:

1. **Consistent Project-Root Environment Loading:**
   Ensured that the project-root `.env` (and `backend/.env` as fallback) is loaded reliably upon server startup and service instantiation, regardless of whether the SQLite database already contains shops. Enforced `override=False` to preserve environment variables provided directly by the container or deployment platform.
2. **Graceful Concurrent First-Shop Setup:**
   Handled race conditions during simultaneous initial shop creation in both the automated seed path (`backend/database/db.py`) and the CLI setup utility (`scripts/setup_first_shop.py`). If two processes attempt first-run initialization simultaneously, SQLite primary key and unique constraints are enforced, collisions are caught, and the losing process exits or continues with an informative error rather than crashing with an unhandled `sqlite3.IntegrityError`.

---

## 2. Files Changed and Exact Modifications

### 2.1 `backend/main.py`
- **File Reference:** [`backend/main.py#L14-L21`](file:///C:/Programs/Project/Bolti-Slip/backend/main.py#L14-L21)
- **Change Description:**
  - Added `load_dotenv` for `PROJECT_ROOT / ".env"` and `PROJECT_ROOT / "backend" / ".env"` at module top, before application and router instantiation.
  - Specified `override=False` so deployment/hosting environment variables are never overwritten.
```python
from pathlib import Path
from dotenv import load_dotenv

# Ensure root .env and backend/.env are loaded without overriding existing deployment env vars
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)
```

### 2.2 `backend/database/db.py`
- **File Reference:** [`backend/database/db.py#L18-L34`](file:///C:/Programs/Project/Bolti-Slip/backend/database/db.py#L18-L34) and [`backend/database/db.py#L82-L102`](file:///C:/Programs/Project/Bolti-Slip/backend/database/db.py#L82-L102)
- **Change Description:**
  - Standardized project-root path resolution:
    `_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent`
    `_DB_PATH = _PROJECT_ROOT / "bolti_slip.db"`
  - Added universal `load_dotenv(_PROJECT_ROOT / ".env", override=False)` at the beginning of `sync_init_db()` so that `.env` is loaded even when `shop_count > 0`.
  - Wrapped `INSERT INTO shops (id, username, password_hash, ...)` in a `try ... except sqlite3.IntegrityError as ie:` block.
  - If an `IntegrityError` occurs, queries `SELECT COUNT(*) FROM shops`. If `> 0`, logs an informational message indicating concurrent startup creation and proceeds cleanly. If count is 0, re-raises `ie` to avoid suppressing unrelated database errors.

### 2.3 `backend/services/prisma.py`
- **File Reference:** [`backend/services/prisma.py#L94-L108`](file:///C:/Programs/Project/Bolti-Slip/backend/services/prisma.py#L94-L108)
- **Change Description:**
  - Fixed path resolution when `env_path is None`. Instead of looking only at `backend/.env`, it resolves `project_root = Path(__file__).resolve().parent.parent.parent` and loads `project_root / ".env"` followed by `project_root / "backend" / ".env"`.
  - Used `override=False` to preserve existing environment variables.
  - Updated docstring to document default search path.

### 2.4 `backend/services/timbre.py`
- **File Reference:** [`backend/services/timbre.py#L166-L180`](file:///C:/Programs/Project/Bolti-Slip/backend/services/timbre.py#L166-L180)
- **Change Description:**
  - Fixed path resolution when `env_path is None`. Resolves `project_root = Path(__file__).resolve().parent.parent.parent` and loads `project_root / ".env"` followed by `project_root / "backend" / ".env"`.
  - Used `override=False` to preserve existing environment variables.
  - Updated docstring to document default search path.

### 2.5 `scripts/setup_first_shop.py`
- **File Reference:** [`scripts/setup_first_shop.py#L80-L110`](file:///C:/Programs/Project/Bolti-Slip/scripts/setup_first_shop.py#L80-L110)
- **Change Description:**
  - Wrapped `INSERT INTO shops (id, username, ...)` in `try ... except sqlite3.IntegrityError as ie:`.
  - If `ie` is caught, verifies `SELECT COUNT(*) FROM shops`. If `> 0`, raises `PermissionError`:
    `"Setup aborted: A shop account was created concurrently by another process. This setup script only runs on a fresh database to prevent account takeover or password overwrites."`
  - Re-raises `ie` if `COUNT(*) == 0` so unrelated constraint violations are not masked.

---

## 3. Test Commands and Actual Results

All testing was executed against isolated temporary SQLite databases. No destructive modifications were performed against `bolti_slip.db`.

### 3.1 Suite 1: Batch 1.2 Dedicated Verification Tests
- **Command:** `.venv\Scripts\python.exe scripts/test_batch1_2_fixes.py`
- **Result:** **18/18 PASSED** (Exit code 0)
- **Summary of Verifications:**
  - `[PASS]` At least one worker created the seed shop under 5 concurrent threads
  - `[PASS]` All 5 concurrent workers completed safely without unhandled crashes (`['CREATED', 'HANDLED_GRACEFULLY', ...]`)
  - `[PASS]` Exactly 1 shop exists in shops table (no duplicate or corrupted rows)
  - `[PASS]` Shop ID is 1 and username is 'sharma'
  - `[PASS]` Password hash is intact and verifies correctly
  - `[PASS]` Exactly 1 concurrent worker succeeded in CLI setup
  - `[PASS]` All 3 losing concurrent workers received clean `PermissionError` (no unhandled `IntegrityError`)
  - `[PASS]` `PermissionError` message clearly explains setup abortion
  - `[PASS]` Database contains exactly 1 shop record after concurrent CLI attempts
  - `[PASS]` Test DB prepared with `shop_count = 1`
  - `[PASS]` `sync_init_db()` reliably loads root `.env` when database already contains shops
  - `[PASS]` `load_dotenv(override=False)` preserved existing deployment environment variable
  - `[PASS]` `PrismaService` successfully initialized and loaded `GNANI_API_KEY_ID` from environment
  - `[PASS]` `TimbreService` successfully initialized and loaded `GNANI_API_KEY_ID` from environment
  - `[PASS]` Live database shops intact: Sharma + Test accounts preserved
  - `[PASS]` Sharma Electronics account (`id=1`) preserved in live database
  - `[PASS]` All 9 live tickets completely preserved
  - `[PASS]` All live customers completely preserved

### 3.2 Suite 2: Full Seed Setup Regression Tests
- **Command:** `.venv\Scripts\python.exe scripts/test_seed_setup.py`
- **Result:** **16/16 PASSED** (Exit code 0)
- **Covered Areas:**
  - Existing database preservation
  - Guard against setup takeover on existing DB
  - Fresh DB without seed password creates 0 shops
  - Fresh DB with valid seed password creates 1 shop with valid hash
  - Fresh DB with invalid seed password (<6 chars) rejected
  - CLI setup validation (<3 chars username, <6 chars password)
  - CLI duplicate setup rejected
  - Hardcoded secret absence check (`Sharma@123` removed)

### 3.3 Suite 3: Batch 1 Security Regression Tests
- **Command:** `.venv\Scripts\python.exe scripts/test_batch1_security.py` (with `BypassSandbox: true` for local socket binding)
- **Result:** **33/33 PASSED** (Exit code 0)
- **Covered Areas:**
  - FastAPI app instance and route registration
  - Speech endpoints (`/api/transcribe`, `/api/speak`, `/api/tickets/{id}/confirm`) 401 Unauthorized enforcement
  - Multi-session management, password change, and other-session revocation
  - Rate limiting on `/api/auth/login` (10/min per IP, 429 response)
  - Registration unblocked while login is rate-limited
  - Seed password removal and database preservation

### 3.4 Suite 4: Frontend Production Build
- **Command:** `npm --prefix frontend run build`
- **Result:** **SUCCESS** (Exit code 0)
- **Output:**
  - `✓ 63 modules transformed.`
  - `dist/index.html 1.98 kB`
  - `dist/assets/index-DPdU0Lzn.js 280.75 kB (gzip: 78.12 kB)`
  - `PWA v2.0.0 precache generated (14 entries, 345.23 KiB)`

---

## 4. Live Database Zero-Modification Verification

Inspection of `bolti_slip.db` confirmed that no live data was altered or deleted during this batch:

| Entity | Expected | Verified in `bolti_slip.db` | Status |
|---|:---:|:---:|:---:|
| **Primary Seed Shop (`id=1`)** | Sharma Electronics / `sharma` | `(1, 'sharma', 'Sharma Electronics', 'Rajesh Sharma', '9876543210')` | **Preserved** |
| **Secondary Test Shop (`id=2`)** | Test Electronics / `testshop` | `(2, 'testshop', 'Test Electronics', 'Test Owner', None)` | **Preserved** |
| **Total Repair Tickets** | 9 (`BLT-0001` - `BLT-0009`) | 9 records | **Preserved** |
| **Total Customers** | >= 3 | 4 records | **Preserved** |
| **Password Hashes** | Unmodified PBKDF2 hashes | Identical to pre-audit hashes | **Preserved** |

---

## 5. Remaining Warnings and Observations

1. **`.env` Line 4 Formatting:**
   `python-dotenv` logs `python-dotenv could not parse statement starting at line 4` because line 4 of `.env` contains an extraneous string snippet (`ding (30%)...`). `python-dotenv` safely skips this unparseable line and successfully parses `GNANI_API_KEY_ID`. When convenient, the shop owner can remove this line from their local `.env`.
2. **Production Deployment CORS:**
   In [`backend/main.py`](file:///C:/Programs/Project/Bolti-Slip/backend/main.py), CORS allows `localhost:5173`, `127.0.0.1:5173`, and `localhost:3000`. When deploying Bolti Slip to a remote production domain, the domain should be added to `allow_origins`.

---

## 6. Conclusion

Batch 1.2 corrections have been fully implemented and verified. Both findings from `BATCH_1_1_READ_ONLY_REVIEW.md` are resolved. The application is robust under concurrent execution and environment variable resolution.
