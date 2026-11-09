# Bolti Slip — Batch 1.1: First-Run Seed Account & Setup Fix Report

**Date:** 2026-11-09  
**Milestone:** Security Fixes — Batch 1.1 (First-Run Seed & Account Setup)  
**Project:** `C:\Programs\Project\Bolti-Slip`  
**Status:** ALL TESTS PASSED (16/16 Seed Setup Tests + 33/33 Batch 1 Security Tests + Frontend Production Build)

---

## 1. Executive Summary

In Batch 1, the hardcoded password `"Sharma@123"` was successfully removed from `backend/database/db.py` and replaced with an environment variable check (`BOLTI_SEED_PASSWORD`) with a fallback to `secrets.token_urlsafe(16)`. However, generating an unretrievable random secret on a fresh installation without user knowledge could leave the system inaccessible on first run.

**Batch 1.1 resolves this issue completely without compromising security:**
1. **No Inaccessible Default Accounts:** If `BOLTI_SEED_PASSWORD` is not configured, the backend **no longer silently generates an inaccessible account**. The `shops` table remains empty, leaving the system clean.
2. **Standardized Password Validation:** If `BOLTI_SEED_PASSWORD` is provided, it is strictly validated against the exact same rules as standard registration (minimum 6 characters, maximum 128 characters) before hashing with PBKDF2-HMAC-SHA256 (600,000 rounds). Invalid values are rejected and skipped.
3. **Explicit Setup Paths:** Three explicit, safe, and documented setup paths are provided for first-time shop owners:
   - **Web UI Registration:** Open `/register` to create the initial shop account directly in the browser.
   - **CLI First-Run Setup Tool (`scripts/setup_first_shop.py`):** Interactive or scripted command-line setup with strict input validation and collision checks.
   - **Automated Environment Variable (`BOLTI_SEED_PASSWORD`):** For automated/containerized provisioning.
4. **Takeover Protection:** The setup script and automatic seed block enforce a strict guard: they **only execute when `COUNT(*) FROM shops == 0`**. If any shop exists, the setup mechanism immediately halts to prevent account takeover or password overwrites.
5. **Full Data Preservation:** All existing database records (`bolti_slip.db`), existing shops (`sharma`, `testshop`), existing passwords, and all 8 original repair tickets are completely preserved and untouched.

---

## 2. Files Modified

| File | Type | Changes |
|------|------|---------|
| `backend/database/db.py` | Modified | Replaced `secrets.token_urlsafe` fallback with an explicit check. When `BOLTI_SEED_PASSWORD` is missing, no account is created. Added length validation (6-128 chars). Added safety check ensuring legacy ticket backfill only runs if `shop_id = 1` exists. Loaded `.env` files via `python-dotenv`. |
| `scripts/setup_first_shop.py` | New file | Safe first-run CLI setup utility with input validation (username 3-50 chars, password 6-128 chars), PBKDF2 hashing, and a strict guard preventing execution on databases with existing shops. |
| `.env.example` | Modified | Updated documentation detailing first-run options, placeholder keys, and security instructions. Contains zero secrets. |
| `README.md` | Modified | Documented complete first-run setup procedures (Web UI, CLI, and Environment Variable) and testing instructions. |
| `scripts/test_seed_setup.py` | New test file | Automated test suite (16 tests) verifying existing DB preservation, takeover protection, fresh DB behavior (with/without env variable), validation, and absence of hardcoded secrets. |

---

## 3. Exact Setup Behavior

```
                        ┌─────────────────────────────────┐
                        │   Database Migration / Startup  │
                        └────────────────┬────────────────┘
                                         │
                                         ▼
                             ┌───────────────────────┐
                             │ Any shops in database?│
                             └───────────┬───────────┘
                           Yes           │           No
              ┌──────────────────────────┘           └──────────────────────────┐
              ▼                                                                 ▼
┌───────────────────────────┐                                      ┌────────────────────────┐
│  Skip seed initialization │                                      │ BOLTI_SEED_PASSWORD in │
│  Preserve existing shops  │                                      │      environment?      │
│  Preserve all passwords   │                                      └───────────┬────────────┘
└───────────────────────────┘                                     Yes          │          No
                                                       ┌───────────────────────┘          └───────────────────────────┐
                                                       ▼                                                              ▼
                                       ┌───────────────────────────────┐                            ┌─────────────────────────────────┐
                                       │ Meets password requirements?  │                            │    DO NOT create default shop   │
                                       │     (6 <= len <= 128)         │                            │    Shops table remains empty    │
                                       └───────────────┬───────────────┘                            └────────────────┬────────────────┘
                                              Yes      │      No                                                     │
                                       ┌───────────────┘      └────────────────┐                                     ▼
                                       ▼                                       ▼                    ┌─────────────────────────────────┐
                      ┌─────────────────────────────────┐       ┌──────────────────────────────┐    │ First shop setup options:       │
                      │ Hash with PBKDF2-SHA256 (600k)  │       │ Log warning (no password log)│    │ 1. Web UI: Register at /register│
                      │ Insert initial shop 'sharma'    │       │ Skip creation; DB clean      │    │ 2. CLI: setup_first_shop.py     │
                      └─────────────────────────────────┘       └──────────────────────────────┘    └─────────────────────────────────┘
```

---

## 4. Tests Actually Executed

### Suite A: Seed Setup & Protection Tests (`scripts/test_seed_setup.py`)
Executed with: `.venv\Scripts\python.exe scripts\test_seed_setup.py`

| # | Test Suite | Test Assertion | Result |
|---|------------|----------------|--------|
| 1 | Existing DB Preservation | Existing shops and password hashes completely unchanged | ✅ PASS |
| 2 | Existing DB Preservation | Existing tickets completely unchanged (9 tickets verified) | ✅ PASS |
| 3 | Existing DB Preservation | Sharma shop account preserved (id=1) | ✅ PASS |
| 4 | Takeover Protection | `setup_first_shop` correctly blocked on existing DB (PermissionError) | ✅ PASS |
| 5 | Fresh DB without Env | Fresh DB without `BOLTI_SEED_PASSWORD` leaves shops count = 0 | ✅ PASS |
| 6 | Fresh DB with Env | Fresh DB with `BOLTI_SEED_PASSWORD` creates exactly 1 seed shop | ✅ PASS |
| 7 | Fresh DB with Env | Seed shop username ('sharma') and shop_name correctly configured | ✅ PASS |
| 8 | Fresh DB with Env | Configured password successfully verifies against stored PBKDF2 hash | ✅ PASS |
| 9 | Fresh DB with Env | Plaintext password is NOT stored in the database | ✅ PASS |
| 10 | Fresh DB with Invalid Env | Invalid `BOLTI_SEED_PASSWORD` (< 6 chars) rejected; 0 shops created | ✅ PASS |
| 11 | CLI Setup Validation | `validate_username` rejects username with length < 3 | ✅ PASS |
| 12 | CLI Setup Validation | `validate_password` rejects password with length < 6 | ✅ PASS |
| 13 | CLI Setup Validation | `setup_first_shop` creates first shop on fresh DB | ✅ PASS |
| 14 | CLI Setup Validation | Second `setup_first_shop` call on same DB correctly rejected | ✅ PASS |
| 15 | Hardcoded Secret Check | No `'Sharma@123'` in `backend/database/db.py` | ✅ PASS |
| 16 | Hardcoded Secret Check | No `'Sharma@123'` in `.env.example` | ✅ PASS |

**Total Suite A:** 16 Tests | **Passed:** 16 | **Failed:** 0

---

### Suite B: Batch 1 Regression Suite (`scripts/test_batch1_security.py`)
Executed with: `.venv\Scripts\python.exe scripts\test_batch1_security.py`

- Route registration & app import: **10/10 PASSED**
- Speech API authentication (transcribe, speak, confirm require auth): **5/5 PASSED**
- Password change & multi-session revocation: **10/10 PASSED**
- Login rate limiting (10 attempts/min, HTTP 429 response): **4/4 PASSED**
- Seed password removal & database preservation: **4/4 PASSED**

**Total Suite B:** 33 Tests | **Passed:** 33 | **Failed:** 0

---

### Suite C: Frontend Production Build
Executed with: `npm --prefix frontend run build`

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
✓ built in 5.28s

PWA v2.0.0
mode      generateSW
precache  14 entries (345.23 KiB)
files generated
  dist/sw.js
  dist/workbox-796b0218.js
```
**Status: ✅ SUCCESS (Exit code 0, 0 errors, service worker generated)**

---

## 5. Security & Verification Checklist

- [x] Hardcoded password `Sharma@123` is completely removed.
- [x] No plaintext passwords are stored in SQLite (all PBKDF2-HMAC-SHA256 with 32-byte salt).
- [x] No secrets or passwords appear in terminal outputs, logs, or reports.
- [x] No silent inaccessible accounts are created when `BOLTI_SEED_PASSWORD` is absent.
- [x] Password length validation (min 6, max 128 characters) enforced identically on all creation paths.
- [x] Setup script is blocked with `PermissionError` if any shop accounts already exist.
- [x] Existing `sharma` account, `testshop` account, and all 8 original repair tickets in `bolti_slip.db` are preserved.
- [x] `.env.example` and `README.md` updated with placeholder documentation.
- [x] No commits, pushes, or deployments were performed.

---

## 6. Remaining Limitations & Next Steps

1. **Production Domain CORS:** `backend/main.py` currently permits localhost origins. The production domain or tunnel hostname should be added to `allow_origins` upon public hosting.
2. **Automated DB Snapshotting:** A recurring backup cron job (e.g. `sqlite3 bolti_slip.db ".backup backup.db"`) is recommended for production disaster recovery.
