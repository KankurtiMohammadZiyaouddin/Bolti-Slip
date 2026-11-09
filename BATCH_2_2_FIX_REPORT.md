# BATCH 2.2 — Test Database Isolation, Backup Filename Uniqueness & Env Cleanup Report

**Date:** 2026-11-09  
**Project:** Bolti Slip  
**Project Path:** `C:\Programs\Project\Bolti-Slip`  
**Python Runtime:** Python 3.14.0 (`.venv\Scripts\python.exe`)  
**Status:** All Fixes Applied & Verified (100% Pass)

---

## 1. Executive Summary

Batch 2.2 resolves the issues identified during the Batch 2.1 Read-Only Review:
1. **Test Database Isolation:** Completely isolated `scripts/test_batch1_security.py` from the production SQLite database (`bolti_slip.db`). All HTTP registration, session creation, password changes, and rate limiting tests now execute against an isolated temporary SQLite database created via `tempfile`. A safety assertion enforces this boundary at runtime.
2. **Backup Filename Process Uniqueness:** Updated `backend/database/backup.py` to include the operating system process ID (`os.getpid()`) in backup filenames (`bolti_slip_backup_{YYYYMMDD}_{HHMMSS}_{pid}.db`). If multiple backups occur within the exact same second from the same process, a microsecond suffix is appended. The retention matcher regex (`BACKUP_FILENAME_REGEX`) was updated to cleanly match legacy (no PID), standard (with PID), and sub-second (with PID and microsecond) backup files.
3. **Root `.env` Syntax Correction:** Safely stripped the malformed line 4 (`ding (30%)...`) from the root `.env` file without altering or exposing any sensitive credentials.
4. **Live Database Integrity:** Verified that `bolti_slip.db` remained completely untouched across all test executions (13 shops, 9 tickets, 4 customers preserved).

---

## 2. Detailed Changes

### Part 1: Test Database Isolation (`scripts/test_batch1_security.py`)
- **Root Cause:** In earlier runs, `TestClient(app)` used the default `_DB_PATH` in `backend/database/db.py`, causing registration tests (`POST /api/auth/register`) to write temporary test shop records (`tuser_*`, `reg_user_*`) into `bolti_slip.db`.
- **Solution Applied:**
  - Before importing `app` from `backend.main`, a dedicated temporary directory and temporary database path (`_TEMP_DB_PATH`) are generated.
  - The module-level `_DB_PATH` attribute in `backend.database.db` is monkeypatched to `_TEMP_DB_PATH`.
  - Added an explicit safety assertion:
    ```python
    assert _db_mod._DB_PATH.resolve() != (PROJECT_ROOT / "bolti_slip.db").resolve(), \
        "SAFETY: Tests must not use live database!"
    ```
  - Schema migrations are explicitly run against the temporary database via `_db_mod.sync_init_db()` before test client execution.
  - Registered an `atexit` cleanup handler `_cleanup_test_db()` to restore the original `_DB_PATH` and remove temporary database/WAL/SHM files.
  - Test Suite 5 intentionally continues to perform read-only verification of the real `bolti_slip.db` using explicit connection strings to confirm real database preservation.

### Part 2: Backup Filename Process Uniqueness (`backend/database/backup.py`)
- **Root Cause:** Backup filenames previously formatted as `bolti_slip_backup_{timestamp}.db` could collide if multiple worker processes executed backups within the same UTC second.
- **Solution Applied:**
  - Integrated `os.getpid()` into backup filename formatting:
    ```python
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    pid = os.getpid()
    target_name = f"bolti_slip_backup_{timestamp_str}_{pid}.db"
    target_path = dest_dir / target_name

    if target_path.exists():
        micro_str = f"{datetime.now(timezone.utc).microsecond:06d}"
        target_name = f"bolti_slip_backup_{timestamp_str}_{pid}_{micro_str}.db"
        target_path = dest_dir / target_name
    ```
  - Updated retention regex in `backend/database/backup.py`:
    ```python
    BACKUP_FILENAME_REGEX = re.compile(r"^bolti_slip_backup_\d{8}_\d{6}(?:_\d+)*\.db$")
    ```
    This pattern accepts zero or more numeric suffixes, seamlessly supporting:
    - Legacy backups: `bolti_slip_backup_20261109_120000.db`
    - Standard PID backups: `bolti_slip_backup_20261109_120000_12345.db`
    - Sub-second microsecond backups: `bolti_slip_backup_20261109_120000_12345_678901.db`
  - Added new test section `PART A.2: BACKUP FILENAME PID UNIQUENESS` to `scripts/test_batch2_security.py` verifying PID inclusion, regex compatibility, simulated same-second multi-process creation, and malformed filename rejection.

### Part 3: Environment File Cleanup (`.env`)
- Removed extraneous terminal copy-paste artifact on line 4 (`ding (30%)...`).
- Verified that `python-dotenv` loads without parser warnings.
- Preserved existing configuration and secrets without printing or exposing them.

---

## 3. Test Verification Suite Results

All test suites were executed using `.venv\Scripts\python.exe`.

| Test Suite Script | Focus Area | Tests Passed | Tests Failed | Status |
| :--- | :--- | :---: | :---: | :---: |
| `scripts/test_batch1_security.py` | Auth, rate limiting, session revocation, speech endpoint auth (isolated DB) | 33 | 0 | **PASS** |
| `scripts/test_batch2_security.py` | Automated backups, PID uniqueness, retention, CORS security, DB checks | 31 | 0 | **PASS** |
| `scripts/test_seed_setup.py` | First-run seed setup, password rules, account takeover protection | 16 | 0 | **PASS** |
| `scripts/test_batch1_2_fixes.py` | Concurrent setup safety, `.env` loading, Prisma/Timbre API key loading | 18 | 0 | **PASS** |
| `npm --prefix frontend run build` | Frontend TypeScript & Vite production build | All chunks | 0 | **PASS** |

**Total Automated Tests Passed:** 98 / 98 (100%)

---

## 4. Live Database Verification (`bolti_slip.db`)

Direct read-only inspection was performed before running tests and after completing all test executions:

| Table | Pre-Batch 2.2 Baseline | Post-Batch 2.2 Final Count | Discrepancy | Integrity Status |
| :--- | :---: | :---: | :---: | :---: |
| `shops` | 13 | 13 | 0 | **UNTOUCHED** |
| `tickets` | 9 | 9 | 0 | **UNTOUCHED** |
| `customers` | 4 | 4 | 0 | **UNTOUCHED** |

### Verified Records:
- **Shop ID 1:** `sharma` (`Sharma Electronics`, `Rajesh Sharma`) preserved.
- **Shop ID 2:** `devshop` (`Sharma Electronics`, `Rajesh Sharma`) preserved.
- **Shops 3–13:** Previous test artifacts preserved (no new test shops added).
- **Tickets:** BLT-0001 through BLT-0009 completely intact.
- **Customers:** All 4 customer profiles intact.

---

## 5. Security & Safety Compliance

- [x] **No test writes to live database:** All dynamic test shop creation in `test_batch1_security.py` is redirected to an isolated temporary database.
- [x] **Safety assertion active:** Direct test initialization assertion guarantees failure if `_DB_PATH` points to `bolti_slip.db`.
- [x] **Process ID uniqueness:** Multi-process backups in the same second produce distinct filenames without collisions.
- [x] **Zero deletion of live data:** No database records were deleted, reset, or migrated.
- [x] **No secret exposure:** Passwords and API keys remain unexposed in logs and reports.
- [x] **No deployment actions:** No Git commit, push, or cloud deployment was performed.
