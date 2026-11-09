# PostgreSQL Migration & Production Deployment Guide: Render + Neon

**Project:** Bolti Slip  
**Date:** 2026-11-09  
**Runtime:** Python 3.14.0 (`.venv\Scripts\python.exe`)  
**Status:** Architecture Implemented, Schema Validated & Tooling Verified (100% Pass)  
**Live SQLite Database:** Completely Untouched (2 shops, 9 tickets, 4 customers, 5 sessions)  
**Live Neon Database:** Zero Connections or Modifications Made During Implementation

---

## 1. Executive Summary

Bolti Slip has been prepared for production deployment on Render with a managed Neon PostgreSQL database while maintaining complete local development support for SQLite.

Key achievements across Steps 1 through 5:
1. **Multi-Engine Async Architecture:** Added `asyncpg>=0.30.0` alongside `aiosqlite`. SQLite remains the automatic default when `DATABASE_URL` is omitted.
2. **Transparent Query & Parameter Adapter:** Implemented `backend/database/adapter.py` providing token-safe parameter translation (`?` -> `$1, $2, ...`), automatic `INSERT ... RETURNING id` handling for `cursor.lastrowid`, case-insensitive username normalization (`LOWER(username) = LOWER(?)`), and `Decimal` to `float` numeric serialization.
3. **Idempotent PostgreSQL DDL Schema:** Created `backend/database/migrations_pg/001_initial_schema.sql` defining `shops`, `customers`, `tickets`, and `sessions` with procedural `update_updated_at_column()` triggers, foreign-key cascade rules, and case-insensitive unique indexes.
4. **Idempotent Data Migration Tool:** Created `scripts/migrate_sqlite_to_pg.py` with conflict detection, read-only SQLite extraction, dry-run simulation mode, and PostgreSQL `BIGSERIAL` sequence synchronization.
5. **Regression Verification:** All 152 automated tests and the frontend production build passed with zero regressions.

---

## 2. Inventory of Changes

| Component / File | Status | Description |
| :--- | :---: | :--- |
| [`backend/requirements.txt`](file:///C:/Programs/Project/Bolti-Slip/backend/requirements.txt) | **Modified** | Added `asyncpg>=0.30.0` while preserving `aiosqlite`. |
| [`backend/database/adapter.py`](file:///C:/Programs/Project/Bolti-Slip/backend/database/adapter.py) | **Created** | Multi-engine abstraction layer (`RowWrapper`, `CursorWrapper`, `PostgresConnectionWrapper`, `convert_qmark_to_dollar`, `mask_database_url`). |
| [`backend/database/db.py`](file:///C:/Programs/Project/Bolti-Slip/backend/database/db.py) | **Modified** | Multi-engine pool management; defaults to SQLite, switches to `asyncpg` when `DATABASE_URL` is set. |
| [`backend/main.py`](file:///C:/Programs/Project/Bolti-Slip/backend/main.py) | **Modified** | Lifespan handler cleanly calls `await close_db()` on application shutdown. |
| [`backend/database/migrations_pg/001_initial_schema.sql`](file:///C:/Programs/Project/Bolti-Slip/backend/database/migrations_pg/001_initial_schema.sql) | **Created** | Idempotent PostgreSQL DDL schema with constraints, triggers, and indexes. |
| [`backend/database/schema_pg.py`](file:///C:/Programs/Project/Bolti-Slip/backend/database/schema_pg.py) | **Created** | Migration runner and `information_schema` schema validator. |
| [`backend/routers/auth.py`](file:///C:/Programs/Project/Bolti-Slip/backend/routers/auth.py) | **Modified** | Replaced `COLLATE NOCASE` with ANSI-standard `LOWER(username) = LOWER(?)`. |
| [`.env.example`](file:///C:/Programs/Project/Bolti-Slip/.env.example) | **Modified** | Documented PostgreSQL `DATABASE_URL` format. |
| [`scripts/migrate_sqlite_to_pg.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/migrate_sqlite_to_pg.py) | **Created** | Transactional, conflict-detecting SQLite-to-PostgreSQL data transfer utility. |
| [`scripts/test_adapter.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_adapter.py) | **Created** | 28 automated tests covering parameter conversion, row mapping, and query translation. |
| [`scripts/test_postgres_schema.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_postgres_schema.py) | **Created** | 18 tests verifying PostgreSQL schema structure and migration idempotency. |
| [`scripts/test_migration_script.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_migration_script.py) | **Created** | 8 unit tests covering read-only extraction, conflict detection, dry run, and sequence resets. |

---

## 3. Data Migration Architecture & Safety Guarantees

The migration utility [`scripts/migrate_sqlite_to_pg.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/migrate_sqlite_to_pg.py) enforces strict safety controls:

1. **Read-Only SQLite Access:** Opens SQLite via URI `file:...bolti_slip.db?mode=ro`, guaranteeing zero disk writes to the source database.
2. **Strict Dependency Order:** Migrates `shops` -> `customers` -> `tickets` -> `sessions` to respect foreign keys.
3. **Conflict Detection vs. Idempotency:**
   - If an existing record in PostgreSQL has matching ID and primary attributes, it is identified as `already_migrated` and safely skipped without re-inserting.
   - If an existing record in PostgreSQL has divergent data (e.g. same ID with different username, or same username with different ID), it raises `MigrationConflictError` and halts immediately.
   - Never executes silent overwrites or broad replacement.
4. **BIGSERIAL Sequence Synchronization:**
   After inserting records with preserved explicit IDs (Shop 1, Shop 2, Tickets 1–9, etc.), the script executes:
   ```sql
   SELECT setval(pg_get_serial_sequence('shops', 'id'), COALESCE((SELECT MAX(id) FROM shops), 1));
   SELECT setval(pg_get_serial_sequence('customers', 'id'), COALESCE((SELECT MAX(id) FROM customers), 1));
   SELECT setval(pg_get_serial_sequence('tickets', 'id'), COALESCE((SELECT MAX(id) FROM tickets), 1));
   ```
   This prevents subsequent new registrations or ticket creations on Neon from throwing duplicate key errors.
5. **Single Atomic Transaction:** All table insertions and sequence updates execute inside a single transaction. Any failure triggers an immediate rollback.
6. **Dry-Run Mode (`--dry-run`):** Performs full extraction, schema verification, conflict inspection, and transaction execution before intentionally rolling back without saving changes.

---

## 4. Test Verification Suite Results

All test suites were executed against the Python 3.14 virtual environment:

| Test Suite Script | Focus Area | Tests Passed | Status |
| :--- | :--- | :---: | :---: |
| [`scripts/test_migration_script.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_migration_script.py) | SQLite read-only extraction, conflict detection, dry run, sequence sync | 8 / 8 | **PASS** |
| [`scripts/test_postgres_schema.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_postgres_schema.py) | PostgreSQL DDL definitions, trigger functions, cascade rules, idempotency | 18 / 18 | **PASS** |
| [`scripts/test_adapter.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_adapter.py) | Parameter scanner, `RowWrapper`, `RETURNING id`, `Decimal` to `float`, masking | 28 / 28 | **PASS** |
| [`scripts/test_seed_setup.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_seed_setup.py) | Seed account creation, takeover protection, credential validation | 16 / 16 | **PASS** |
| [`scripts/test_batch1_2_fixes.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_batch1_2_fixes.py) | Concurrency safety, `.env` loading, Prisma/Timbre key initialization | 18 / 18 | **PASS** |
| [`scripts/test_batch1_security.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_batch1_security.py) | Speech auth, login rate limits, password change session revocation (isolated DB) | 33 / 33 | **PASS** |
| [`scripts/test_batch2_security.py`](file:///C:/Programs/Project/Bolti-Slip/scripts/test_batch2_security.py) | Automated backups, PID collision prevention, production CORS enforcement | 31 / 31 | **PASS** |
| `npm --prefix frontend run build` | Frontend TypeScript & Vite production build | All chunks | **PASS** |

**Total Automated Tests Passed:** 152 / 152 (100% Pass)

---

## 5. Live Database Integrity (`bolti_slip.db`)

Direct read-only inspection confirmed the SQLite database is completely untouched:

- **Shops:** Exactly **2** (`sharma` ID 1, `testshop` ID 2)
- **Tickets:** Exactly **9** (`BLT-0001` through `BLT-0009`)
- **Customers:** Exactly **4**
- **Sessions:** Exactly **5**
- **Integrity Check:** `ok`
- **Foreign Key Check:** 0 violations

---

## 6. Exact Step-by-Step Instructions for Production Migration

When you are ready to migrate your data to your Neon PostgreSQL database, execute the following controlled steps:

### Step A: Configure Target Database URL
Ensure your Neon connection URL is defined in the root `.env`:
```bash
DATABASE_URL=postgresql://<user>:<password>@<ep-identifier>.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### Step B: Run Validation Dry-Run
Run the migration script in dry-run mode first:
```powershell
.venv\Scripts\python.exe scripts/migrate_sqlite_to_pg.py --dry-run
```
*Expected Output:*
- Connects to Neon using SSL.
- Creates the PostgreSQL schema idempotently (`run_postgres_migrations`).
- Reads all 2 shops, 4 customers, 9 tickets, and 5 sessions from SQLite.
- Confirms zero conflicts.
- Rolls back transaction cleanly and prints `DRY-RUN COMPLETE: Target PostgreSQL was not modified.`

### Step C: Execute Live Migration
Once the dry-run passes cleanly, execute the live migration:
```powershell
.venv\Scripts\python.exe scripts/migrate_sqlite_to_pg.py
```
*Expected Output:*
```
============================================================
  MIGRATION SUMMARY
============================================================
  shops_inserted: 2
  shops_already_migrated: 0
  customers_inserted: 4
  customers_already_migrated: 0
  tickets_inserted: 9
  tickets_already_migrated: 0
  sessions_inserted: 5
  sessions_already_migrated: 0
============================================================
  SUCCESS: Data migrated and sequences synchronized.
```

### Step D: Render Deployment Configuration
On Render, configure the following Environment Variables in the Web Service settings:
- `DATABASE_URL`: Your Neon PostgreSQL connection string.
- `GNANI_API_KEY_ID`: Your Gnani AI voice API key.
- `BOLTI_ENV`: `production`
- `BOLTI_CORS_ORIGINS`: Your production frontend URL (e.g. `https://bolti-slip.onrender.com`).
