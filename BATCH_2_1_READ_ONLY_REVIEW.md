# BOLTI SLIP — BATCH 2.1 READ-ONLY SECURITY REVIEW

**Audit Target:** Batch 2 Implementation (Database Backups & Production CORS Configuration)  
**Target Path:** `C:\Programs\Project\Bolti-Slip`  
**Audit Mode:** Strict Read-Only (Zero Code Alterations, Zero Database Modifications)  
**Date:** 2026-11-09  
**Auditor:** Senior Application Security & Systems Engineer  
**Overall Verdict:** **ACCEPTABLE_WITH_CONDITIONS** (Production-ready with non-blocking operational improvements)

---

## 1. Executive Summary

This read-only audit evaluated the security, operational reliability, and architectural soundness of the **Batch 2** features:
1. **Automated SQLite Database Backups** ([`backend/database/backup.py`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py))
2. **Production CORS Configuration** ([`backend/config.py`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py), [`backend/main.py`](file:///C:/Programs/Project/Bolti-Slip/backend/main.py))

In addition, two critical diagnostic inquiries were resolved:
- **Live Database Discrepancy:** Complete forensic tracing of why 13 shops existed in `bolti_slip.db` while the summary table listed only 2.
- **Environment Warning:** Root cause identification of `python-dotenv could not parse statement starting at line 4`.

### Overall Verdict: **ACCEPTABLE_WITH_CONDITIONS**
The backup mechanism and CORS security meet all core functional and security specifications. Zero production data was lost, corrupted, or exposed. Two non-blocking operational refinements (in-memory test database isolation and cross-process debounce) are identified for future hardening.

---

## 2. Investigation 1: Live Database Discrepancy (13 vs 2 Shops)

### 2.1 The Issue
The Batch 2 report noted `13 shops found` during test execution, but the final integrity verification table listed only 2 shops (`id=1` Sharma Electronics and `id=2` Test Electronics).

### 2.2 Forensic Inspection of `bolti_slip.db`
A direct read-only query against `bolti_slip.db` (`sqlite3.connect('file:bolti_slip.db?mode=ro', uri=True)`) revealed the following 13 records in the `shops` table:

| ID | Username | Shop Name | Owner Name | Created At (UTC) | Origin / Attribution |
|:---:|---|---|---|---|---|
| **1** | `sharma` | Sharma Electronics | Rajesh Sharma | 2026-11-08T16:31:52Z | **Original Seed Account** (Batch 1) |
| **2** | `testshop` | Test Electronics | Test Owner | 2026-11-08T17:58:30Z | **Permanent Multi-Shop Test Account** (Batch 1) |
| **3** | `tuser_97c5ee13` | Test Shop Revocation | Test Owner | 2026-11-09T00:03:12Z | `test_batch1_security.py` (Run 1, Suite 3) |
| **4** | `reg_user_78e199` | Non-blocked Shop | Test | 2026-11-09T00:03:17Z | `test_batch1_security.py` (Run 1, Suite 4) |
| **5** | `tuser_c8111c0c` | Test Shop Revocation | Test Owner | 2026-11-09T00:03:50Z | `test_batch1_security.py` (Run 2, Suite 3) |
| **6** | `tuser_6063d81c` | Test Shop Revocation | Test Owner | 2026-11-09T00:06:00Z | `test_batch1_security.py` (Run 3, Suite 3) |
| **7** | `reg_user_0fd7b4` | Non-blocked Shop | Test | 2026-11-09T00:06:08Z | `test_batch1_security.py` (Run 3, Suite 4) |
| **8** | `tuser_6b9ccbc3` | Test Shop Revocation | Test Owner | 2026-11-09T00:27:34Z | `test_batch1_security.py` (Run 4, Suite 3) |
| **9** | `reg_user_3c8bdf` | Non-blocked Shop | Test | 2026-11-09T00:27:43Z | `test_batch1_security.py` (Run 4, Suite 4) |
| **10** | `tuser_b54b0dcc` | Test Shop Revocation | Test Owner | 2026-11-09T05:18:27Z | `test_batch1_security.py` (Run 5, Suite 3) |
| **11** | `reg_user_7d7836` | Non-blocked Shop | Test | 2026-11-09T05:18:37Z | `test_batch1_security.py` (Run 5, Suite 4) |
| **12** | `tuser_b820e0ad` | Test Shop Revocation | Test Owner | 2026-11-09T05:38:38Z | `test_batch1_security.py` (Run 6, Suite 3) |
| **13** | `reg_user_541a0b` | Non-blocked Shop | Test | 2026-11-09T05:38:48Z | `test_batch1_security.py` (Run 6, Suite 4) |

### 2.3 Exact Cause Analysis
1. **Did `scripts/test_batch2_security.py` modify the live database?**  
   **NO.** `test_batch2_security.py` executes all backup, write, and restore tests inside isolated `tempfile.TemporaryDirectory()` instances.
2. **Did `scripts/test_batch1_2_fixes.py` or `scripts/test_seed_setup.py` modify the live database?**  
   **NO.** Both use isolated `tempfile.NamedTemporaryFile()` instances for all insert/setup tests.
3. **Which test modified the live database?**  
   [`scripts/test_batch1_security.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_batch1_security.py).  
   In `test_batch1_security.py`:
   - Line 25 imports `from backend.main import app`.
   - Line 54 initializes `client = TestClient(app)`.
   - `app` relies on `backend.database.db.get_db`, which connects directly to `_DB_PATH = bolti_slip.db`.
   - Lines 152–158 register `tuser_<hex>` via `POST /api/auth/register`.
   - Lines 294–299 register `reg_user_<hex>` via `POST /api/auth/register`.
   - Because `test_batch1_security.py` was executed 6 times across regression test cycles, 11 ephemeral test shops were created in `bolti_slip.db`.
4. **Why did the Batch 2 report list only 2 shops in the final table?**  
   The author of `BATCH_2_SECURITY_REPORT.md` presented only the **2 primary application shops** (`id=1` Sharma Electronics and `id=2` Test Electronics) in the summary table to highlight that the permanent production shops were preserved, while the test output in Section 6.1 reported the raw row count of 13.
5. **Impact on Production Data:**  
   Zero original data was overwritten or deleted. All 9 repair tickets (`BLT-0001` through `BLT-0009`) and all original customer records remain 100% intact.

---

## 3. Investigation 2: Backup Safety Verification

| Area | Status | File & Line Reference | Evaluation & Findings |
|---|:---:|---|---|
| **Backup Mechanism** | **PASS** | [`backup.py#L148-L154`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L148-L154) | Uses Python's native `sqlite3.Connection.backup()`. Copies database pages atomically without taking the database offline or locking out concurrent readers. Both connections are explicitly closed in `finally:` blocks. |
| **Completion & Integrity** | **PASS** | [`backup.py#L156-L158`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L156-L158) | Validates that destination file exists and `st_size > 0`. Raises `IOError` and cleans up corrupted/empty files if size verification fails. |
| **Debounce & Duplicate Prevention** | **WARNING** | [`backup.py#L28-L30`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L28-L30)<br>[`backup.py#L120-L127`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L120-L127) | `_last_backup_time` and `_last_backup_path` are in-memory module-level variables. Debounce works within a single process. However, during rapid process restarts or development reloads (`--reload`), the in-memory timer resets, creating a new timestamped backup on every boot. |
| **Concurrent Backup Attempts** | **WARNING** | [`backup.py#L136-L144`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L136-L144) | If two worker processes start in the exact same second, both format `bolti_slip_backup_YYYYMMDD_HHMMSS.db`. While lines 141–144 check `target_path.exists()` and append microseconds, a narrow race condition exists before the first process creates the file. Appending the process ID (`os.getpid()`) to the filename will make it 100% collision-free. |
| **Retention & Live DB Safety** | **PASS** | [`backup.py#L25`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L25)<br>[`backup.py#L61-L67`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L61-L67) | Strict regex `^bolti_slip_backup_\d{8}_\d{6}(?:_\d+)?\.db$` ensures unrelated files (`.txt`, notes, other `.db` files) are never deleted. `item.resolve() == resolved_source` strictly prevents deleting the live active database. |
| **Failure Handling** | **PASS** | [`backup.py#L178-L186`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L178-L186) | Catches all exceptions, logs an error without leaking sensitive credentials or database data, cleans up partial files, and returns `None` without crashing startup. |
| **WAL & SHM Restoration** | **PASS** | [`README.md#L125-L144`](file:///C:/Programs/Project/Bolti-Slip/README.md#L125-L144) | `sqlite3.Connection.backup()` reads through the SQLite pager, creating a standalone, fully-checkpointed database. Manual restore instructions correctly document removing `bolti_slip.db-wal` and `bolti_slip.db-shm` prior to starting the restored database. |
| **Directory & Endpoint Security** | **PASS** | [`.gitignore#L14-L18`](file:///C:/Programs/Project/Bolti-Slip/.gitignore#L14-L18)<br>[`backend/main.py#L75-L88`](file:///C:/Programs/Project/Bolti-Slip/backend/main.py#L75-L88) | Default directory `backups/` is outside frontend webroot. Explicitly excluded from version control via `.gitignore`. No static routes or public API endpoints mount or expose `backups/`. |

---

## 4. Investigation 3: CORS Security Verification

| Area | Status | File & Line Reference | Evaluation & Findings |
|---|:---:|---|---|
| **Production Explicit Origins** | **PASS** | [`config.py#L90-L108`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L90-L108) | In production mode (`BOLTI_ENV=production`), localhost origins are completely stripped. Only origins explicitly defined in `BOLTI_CORS_ORIGINS` are permitted. |
| **Wildcard Disallowed** | **PASS** | [`config.py#L75-L84`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L75-L84) | Wildcard `*` is strictly forbidden in production mode. If provided, it is dropped and logged as a security warning. |
| **Safe Failure on Missing Config** | **PASS** | [`config.py#L106-L113`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L106-L113) | If `BOLTI_ENV=production` but `BOLTI_CORS_ORIGINS` is missing or empty, `allow_origins` defaults to `[]`. All cross-origin browser requests are rejected, and an active security alert is logged. |
| **Development Configuration** | **PASS** | [`config.py#L19-L24`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L19-L24)<br>[`config.py#L100-L104`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L100-L104) | In development mode, standard Vite dev server origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`, `http://127.0.0.1:3000`) are allowed automatically. Custom LAN IPs are also supported. |
| **Credentials & Method/Header Scope** | **PASS** | [`config.py#L26-L28`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L26-L28)<br>[`config.py#L121-L131`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L121-L131) | `allow_credentials` is only enabled when valid explicit origins exist (never with `*`). Methods are restricted to `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]`. Headers are restricted to `["Authorization", "Content-Type", "Accept", "X-Requested-With"]`. |
| **Tamper Resistance** | **PASS** | [`config.py#L86-L92`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L86-L92) | Enforces `http://` or `https://` scheme. Strips trailing slashes to prevent origin header mismatches. Disallows arbitrary schemes (e.g. `javascript:`, `data:`). |

---

## 5. Investigation 4: Environment Warning Analysis

### 5.1 Observation
On every startup and test execution, python outputs:
```text
python-dotenv could not parse statement starting at line 4
```

### 5.2 Forensic Inspection of `.env` (Masked / Read-Only)
Inspection of `.env` in the project root revealed:
- **Line 1:** `# Gnani AI API credentials\n` (Comment)
- **Line 2:** `# Replace the placeholder below with your actual key...\n` (Comment)
- **Line 3:** `GNANI_API_KEY_ID=<REDACTED_API_KEY>\n` (Valid Key-Value pair)
- **Line 4:** `ding (30%)...` (Malformed Text)

### 5.3 Root Cause
The text `ding (30%)...` is an unformatted terminal progress fragment (e.g. from an npm, git, or pip command `Building (30%)...`) that was inadvertently pasted into `.env` below the API key. Because `python-dotenv` expects lines to be comments (`# ...`) or variable definitions (`KEY=VAL`), it emits a warning and safely skips the unparseable line.

### 5.4 Recommended Correction
When convenient, the operator should open `.env` and delete line 4 (`ding (30%)...`). No application code changes are required.

---

## 6. Findings Summary Matrix

| Category | Item | Verdict | File & Line | Notes |
|---|---|:---:|---|---|
| **Database** | Live DB record preservation | **PASS** | `bolti_slip.db` | All 9 original tickets and 4 customers are 100% preserved. |
| **Testing** | Live DB test contamination | **WARNING** | [`test_batch1_security.py#L54`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_batch1_security.py#L54) | `test_batch1_security.py` uses `app` connected to live DB, creating 2 test shop accounts per test run. |
| **Backup** | Online SQLite backup API | **PASS** | [`backup.py#L148-L154`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L148-L154) | Atomic `src_conn.backup(dst_conn)` with explicit connection closure. |
| **Backup** | Startup automation | **PASS** | [`main.py#L22-L28`](file:///C:/Programs/Project/Bolti-Slip/backend/main.py#L22-L28) | Executed in lifespan after migrations. |
| **Backup** | Retention & live DB protection | **PASS** | [`backup.py#L61-L67`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L61-L67) | Live DB protected by absolute path check; unrelated files preserved. |
| **Backup** | Debounce across restarts | **WARNING** | [`backup.py#L28-L30`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L28-L30) | In-memory timer resets on uvicorn `--reload` or process restart. |
| **Backup** | Concurrent worker naming | **WARNING** | [`backup.py#L136-L144`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L136-L144) | Potential same-second filename collision under simultaneous worker boot. |
| **CORS** | Production origin isolation | **PASS** | [`config.py#L90-L108`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L90-L108) | Strict whitelist; localhost origins excluded in production. |
| **CORS** | Wildcard `*` rejection | **PASS** | [`config.py#L75-L84`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L75-L84) | Wildcards forbidden and dropped in production. |
| **CORS** | Safe failure on empty config | **PASS** | [`config.py#L106-L113`](file:///C:/Programs/Project/Bolti-Slip/backend/config.py#L106-L113) | Defaults to `[]`, rejecting all cross-origin requests. |
| **Config** | `.env` line 4 formatting | **WARNING** | `.env#L4` | Stray `ding (30%)...` causes harmless startup warning. |

---

## 7. Recommended Minimal Corrections (Non-Blocking)

These minimal refinements are recommended for the next implementation phase:

1. **Isolate `scripts/test_batch1_security.py` from the Live Database:**
   Update `scripts/test_batch1_security.py` to override `get_db` or point `_DB_PATH` to a temporary SQLite database during test runs:
   ```python
   # In scripts/test_batch1_security.py
   from tempfile import NamedTemporaryFile
   # Point db to isolated test file so test_user and reg_user are not written to bolti_slip.db
   ```
2. **Clean Up Ephemeral Test Shops in `bolti_slip.db`:**
   Execute a safe cleanup query to remove test shops (`id >= 3`) created during regression test runs:
   ```sql
   DELETE FROM shops WHERE id >= 3 AND username LIKE 'tuser_%' OR username LIKE 'reg_user_%';
   ```
3. **Add Process ID to Backup Filename:**
   In [`backend/database/backup.py#L137`](file:///C:/Programs/Project/Bolti-Slip/backend/database/backup.py#L137), include `os.getpid()` to make concurrent worker backups collision-free:
   ```python
   target_name = f"bolti_slip_backup_{timestamp_str}_{os.getpid()}.db"
   ```
4. **Clean Stray Line in `.env`:**
   Delete line 4 (`ding (30%)...`) from `.env` to eliminate the `python-dotenv` startup warning.

---

## 8. Final Sign-Off & Verdict

### Acceptance Verdict: **ACCEPTABLE_WITH_CONDITIONS**
- The Batch 2 implementation is **safe, production-ready, and functionally sound**.
- Backups are created reliably via `sqlite3.Connection.backup()`.
- CORS security enforces strict origin isolation without wildcards.
- No source code, environment files, databases, or tests were modified during this review.
- No Git commit, push, or deployment was performed.
