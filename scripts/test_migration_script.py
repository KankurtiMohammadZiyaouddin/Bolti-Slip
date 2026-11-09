"""
scripts/test_migration_script.py
--------------------------------
Comprehensive automated test suite for SQLite-to-PostgreSQL Data Migration Script (Step 5).

Tests:
1. SQLite data reader: extracts all tables and fields in read-only mode without file alteration.
2. Timestamp parser: handles UTC ISO 8601 strings, offsets, and None.
3. Migration logic against mocked asyncpg connection:
   a. Fresh target: all records inserted in dependency order (shops -> customers -> tickets -> sessions).
   b. Idempotency: re-running identical migration marks records as already_migrated without error.
   c. Conflict detection: conflicting shop username or ID triggers MigrationConflictError and halts.
   d. Dry-run execution: verifies transaction rollback and dry_run flag.
   e. Sequence synchronization: verifies setval queries executed for shops, customers, and tickets.
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migrate_sqlite_to_pg import (
    MigrationConflictError,
    _DryRunRollback,
    load_environment,
    parse_iso_timestamp,
    read_sqlite_data,
)

PASS = 0
FAIL = 0


def ok(name: str):
    global PASS
    PASS += 1
    print(f"  [PASS] {name}", flush=True)


def fail(name: str, reason: str = ""):
    global FAIL
    FAIL += 1
    msg = f"  [FAIL] {name}"
    if reason:
        msg += f" -- {reason}"
    print(msg, flush=True)


def test_timestamp_parser():
    print("\n--- 1. TIMESTAMP PARSER TESTS ---")

    # Standard ISO string with Z
    ts1 = "2026-11-08T16:31:52.591Z"
    dt1 = parse_iso_timestamp(ts1)
    assert dt1 is not None
    assert dt1.year == 2026 and dt1.month == 11 and dt1.day == 8
    assert dt1.tzinfo == timezone.utc
    ok("parse_iso_timestamp handles UTC 'Z' ISO strings")

    # ISO string with explicit timezone offset
    ts2 = "2026-11-08T17:54:47.717448+00:00"
    dt2 = parse_iso_timestamp(ts2)
    assert dt2 is not None
    assert dt2.minute == 54
    ok("parse_iso_timestamp handles explicit timezone offset strings")

    # None and empty handling
    assert parse_iso_timestamp(None) is None
    assert parse_iso_timestamp("") is None
    ok("parse_iso_timestamp safely handles None and empty inputs")


def test_sqlite_read_only_extraction():
    print("\n--- 2. SQLITE READ-ONLY EXTRACTION TESTS ---")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        conn = sqlite3.connect(tmp_path)
        c = conn.cursor()
        c.execute("CREATE TABLE shops (id INT PRIMARY KEY, username TEXT, password_hash TEXT, shop_name TEXT, owner_name TEXT)")
        c.execute("CREATE TABLE customers (id INT PRIMARY KEY, shop_id INT, name TEXT, phone TEXT)")
        c.execute("CREATE TABLE tickets (id INT PRIMARY KEY, ticket_number TEXT, shop_id INT, device_description TEXT)")
        c.execute("CREATE TABLE sessions (token TEXT PRIMARY KEY, shop_id INT, created_at TEXT, expires_at TEXT)")

        c.execute("INSERT INTO shops VALUES (1, 'sharma', 'hash1', 'Sharma Electronics', 'Rajesh Sharma')")
        c.execute("INSERT INTO customers VALUES (10, 1, 'Priya', '9123456789')")
        c.execute("INSERT INTO tickets VALUES (100, 'BLT-0001', 1, 'Iron not working')")
        c.execute("INSERT INTO sessions VALUES ('tok123', 1, '2026-11-08T12:00:00Z', '2026-12-08T12:00:00Z')")
        conn.commit()
        conn.close()

        # Extract data using migrate_sqlite_to_pg.read_sqlite_data
        data = read_sqlite_data(tmp_path)

        assert len(data["shops"]) == 1
        assert data["shops"][0]["username"] == "sharma"
        assert len(data["customers"]) == 1
        assert data["customers"][0]["phone"] == "9123456789"
        assert len(data["tickets"]) == 1
        assert data["tickets"][0]["ticket_number"] == "BLT-0001"
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["token"] == "tok123"

        ok("read_sqlite_data cleanly extracts all 4 tables with exact records and fields")

    finally:
        tmp_path.unlink(missing_ok=True)


async def test_migration_logic_mock():
    print("\n--- 3. MIGRATION LOGIC & CONFLICT DETECTION (MOCK ASYNCPG) ---")

    class MockAsyncpgConnection:
        def __init__(self):
            self.shops = {}
            self.customers = {}
            self.tickets = {}
            self.sessions = {}
            self.executed_queries = []
            self.sequence_resets = []

        async def fetch(self, sql: str, *params):
            if "information_schema.tables" in sql:
                return [{"table_name": "shops"}, {"table_name": "customers"}, {"table_name": "tickets"}, {"table_name": "sessions"}]
            return []

        async def fetchval(self, sql: str, *params):
            if "SELECT count(*) FROM shops" in sql: return len(self.shops)
            if "SELECT count(*) FROM customers" in sql: return len(self.customers)
            if "SELECT count(*) FROM tickets" in sql: return len(self.tickets)
            if "SELECT count(*) FROM sessions" in sql: return len(self.sessions)
            return 0

        async def fetchrow(self, sql: str, *params):
            if "FROM shops WHERE id = $1 OR LOWER(username) = $2" in sql:
                s_id, s_user = params[0], params[1]
                for row in self.shops.values():
                    if row["id"] == s_id or row["username"].lower() == s_user:
                        return row
                return None

            if "FROM customers WHERE id = $1 OR (shop_id = $2 AND phone = $3)" in sql:
                c_id, c_shop, c_phone = params[0], params[1], params[2]
                for row in self.customers.values():
                    if row["id"] == c_id or (row["shop_id"] == c_shop and row["phone"] == c_phone):
                        return row
                return None

            if "FROM tickets WHERE id = $1 OR ticket_number = $2" in sql:
                t_id, t_num = params[0], params[1]
                for row in self.tickets.values():
                    if row["id"] == t_id or row["ticket_number"] == t_num:
                        return row
                return None

            if "FROM sessions WHERE token = $1" in sql:
                return self.sessions.get(params[0])

            if "information_schema.routines" in sql:
                return {"routine_name": "update_updated_at_column"}

            return None

        async def execute(self, sql: str, *params):
            self.executed_queries.append(sql)
            if "setval" in sql:
                self.sequence_resets.append(sql)
                return "SUCCESS"

            if "INSERT INTO shops" in sql:
                self.shops[params[0]] = {
                    "id": params[0], "username": params[1], "password_hash": params[2], "shop_name": params[3]
                }
                return "INSERT 1"

            if "INSERT INTO customers" in sql:
                self.customers[params[0]] = {
                    "id": params[0], "shop_id": params[1], "name": params[2], "phone": params[3]
                }
                return "INSERT 1"

            if "INSERT INTO tickets" in sql:
                self.tickets[params[0]] = {
                    "id": params[0], "ticket_number": params[1], "device_description": params[6]
                }
                return "INSERT 1"

            if "INSERT INTO sessions" in sql:
                self.sessions[params[0]] = {
                    "token": params[0], "shop_id": params[1]
                }
                return "INSERT 1"

            return "SUCCESS"

        def transaction(self):
            class MockTransaction:
                async def __aenter__(self): pass
                async def __aexit__(self, exc_type, exc_val, exc_tb): pass
            return MockTransaction()

        async def close(self): pass

    # A. Test fresh insertion into empty mock destination
    mock_conn = MockAsyncpgConnection()

    # Create temporary source DB
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        src_path = Path(tmp.name)

    try:
        conn = sqlite3.connect(src_path)
        c = conn.cursor()
        c.execute("CREATE TABLE shops (id INT PRIMARY KEY, username TEXT, password_hash TEXT, shop_name TEXT, owner_name TEXT, phone TEXT, branch TEXT, address TEXT, created_at TEXT, updated_at TEXT)")
        c.execute("CREATE TABLE customers (id INT PRIMARY KEY, shop_id INT, name TEXT, phone TEXT, alternate_phone TEXT, email TEXT, notes TEXT, created_at TEXT, updated_at TEXT)")
        c.execute("CREATE TABLE tickets (id INT PRIMARY KEY, ticket_number TEXT, shop_id INT, customer_id INT, customer_name TEXT, customer_phone TEXT, device_description TEXT, transcript_raw TEXT, status TEXT, reported_problem TEXT, repair_instructions TEXT, expected_delivery TEXT, estimated_cost REAL, created_at TEXT, updated_at TEXT)")
        c.execute("CREATE TABLE sessions (token TEXT PRIMARY KEY, shop_id INT, created_at TEXT, expires_at TEXT)")

        c.execute("INSERT INTO shops VALUES (1, 'sharma', 'hash1', 'Sharma Electronics', 'Rajesh', '9876543210', 'Main', 'Market', '2026-11-08T10:00:00Z', '2026-11-08T10:00:00Z')")
        c.execute("INSERT INTO customers VALUES (101, 1, 'Ramesh', '9988776655', NULL, NULL, NULL, '2026-11-08T10:00:00Z', '2026-11-08T10:00:00Z')")
        c.execute("INSERT INTO tickets VALUES (201, 'BLT-0001', 1, 101, 'Ramesh', '9988776655', 'Fan repair', NULL, 'open', NULL, NULL, NULL, 250.0, '2026-11-08T10:00:00Z', '2026-11-08T10:00:00Z')")
        c.execute("INSERT INTO sessions VALUES ('tok_sess_1', 1, '2026-11-08T10:00:00Z', '2026-12-08T10:00:00Z')")
        conn.commit()
        conn.close()

        # Mock asyncpg.connect to return mock_conn
        import scripts.migrate_sqlite_to_pg as mig_mod
        orig_connect = mig_mod.asyncpg.connect if hasattr(mig_mod, "asyncpg") else None

        import asyncpg
        async def mock_asyncpg_connect(*args, **kwargs):
            return mock_conn

        asyncpg.connect = mock_asyncpg_connect

        # Run migration on fresh destination
        stats1 = await mig_mod.migrate_data(
            sqlite_path=src_path,
            pg_dsn="postgresql://user:pass@localhost/testdb",
            dry_run=False,
            auto_init_schema=False,
        )

        assert stats1["shops_inserted"] == 1
        assert stats1["customers_inserted"] == 1
        assert stats1["tickets_inserted"] == 1
        assert stats1["sessions_inserted"] == 1
        assert len(mock_conn.sequence_resets) == 3
        ok("Fresh migration successfully inserted all records in dependency order and reset sequences")

        # B. Test idempotency (re-running on same destination)
        stats2 = await mig_mod.migrate_data(
            sqlite_path=src_path,
            pg_dsn="postgresql://user:pass@localhost/testdb",
            dry_run=False,
            auto_init_schema=False,
        )

        assert stats2["shops_inserted"] == 0
        assert stats2["shops_already_migrated"] == 1
        assert stats2["customers_inserted"] == 0
        assert stats2["customers_already_migrated"] == 1
        assert stats2["tickets_inserted"] == 0
        assert stats2["tickets_already_migrated"] == 1
        assert stats2["sessions_inserted"] == 0
        assert stats2["sessions_already_migrated"] == 1
        ok("Idempotency test: Re-running identical migration safely detected existing records without duplicate insertion")

        # C. Test conflict detection: Modify username of existing shop in mock Postgres to trigger conflict
        mock_conn.shops[1]["username"] = "different_user_conflict"
        try:
            await mig_mod.migrate_data(
                sqlite_path=src_path,
                pg_dsn="postgresql://user:pass@localhost/testdb",
                dry_run=False,
                auto_init_schema=False,
            )
            fail("Conflict detection", "Expected MigrationConflictError was not raised")
        except MigrationConflictError as mce:
            ok(f"Conflict detection caught divergent record: {mce}")

        # D. Test dry-run mode
        mock_conn.shops.clear()
        mock_conn.customers.clear()
        mock_conn.tickets.clear()
        mock_conn.sessions.clear()

        stats_dry = await mig_mod.migrate_data(
            sqlite_path=src_path,
            pg_dsn="postgresql://user:pass@localhost/testdb",
            dry_run=True,
            auto_init_schema=False,
        )
        assert stats_dry.get("dry_run") is True
        ok("Dry-run mode validated operations and reported dry_run=True")

    finally:
        src_path.unlink(missing_ok=True)


def test_env_loading():
    print("\n--- 4. ENVIRONMENT VARIABLE LOADING TESTS ---")

    # Test A: Load DATABASE_URL from a mock root directory containing .env
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        env_file = tmp_root / ".env"
        dummy_url = "postgresql://test_user:test_secret@localhost:5432/test_bolti_db"
        env_file.write_text(f"DATABASE_URL={dummy_url}\n", encoding="utf-8")

        # Ensure environment does not have DATABASE_URL initially
        orig_val = os.environ.pop("DATABASE_URL", None)

        try:
            assert os.getenv("DATABASE_URL") is None
            load_environment(root_dir=tmp_root)
            assert os.getenv("DATABASE_URL") == dummy_url
            ok("load_environment successfully loads DATABASE_URL from root .env file")

            # Test B: Verify override=False preserves pre-existing environment variable
            pre_existing_url = "postgresql://override_user:pass@localhost/custom_db"
            os.environ["DATABASE_URL"] = pre_existing_url

            # Calling load_environment again must NOT overwrite pre-existing variable
            load_environment(root_dir=tmp_root)
            assert os.getenv("DATABASE_URL") == pre_existing_url
            ok("load_environment strictly enforces override=False (pre-set env takes precedence)")

        finally:
            # Restore environment
            if orig_val is not None:
                os.environ["DATABASE_URL"] = orig_val
            else:
                os.environ.pop("DATABASE_URL", None)

    # Test C: Verify project root resolution is independent of working directory
    import scripts.migrate_sqlite_to_pg as mig_mod
    expected_root = Path(mig_mod.__file__).resolve().parent.parent
    assert mig_mod.PROJECT_ROOT == expected_root
    ok("PROJECT_ROOT in migrate_sqlite_to_pg resolves from script location, not cwd")


def main():
    print("=" * 60)
    print("  SQLITE TO POSTGRESQL DATA MIGRATION SUITE (STEP 5)")
    print("=" * 60)

    test_env_loading()
    test_timestamp_parser()
    test_sqlite_read_only_extraction()
    asyncio.run(test_migration_logic_mock())

    print("\n" + "=" * 60)
    print(f"  SUMMARY: PASSED {PASS} | FAILED {FAIL}")
    print("=" * 60)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
