"""
scripts/test_adapter.py
-----------------------
Unit and integration tests for backend/database/adapter.py.
Validates:
1. SQL parameter conversion (? -> $1, $2, ...) with string literals and comments.
2. RowWrapper mapping, dictionary, index, and datetime serialization.
3. CursorWrapper fetchone, fetchall, and lastrowid mechanics.
4. SqliteConnectionWrapper end-to-end against an isolated temporary SQLite DB.
5. PostgresConnectionWrapper parameter conversion and RETURNING id injection.
6. Engine detection and URL credential masking.
"""

import asyncio
import os
import sys
import tempfile
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import aiosqlite
from backend.database.adapter import (
    CursorWrapper,
    PostgresConnectionWrapper,
    RowWrapper,
    SqliteConnectionWrapper,
    convert_qmark_to_dollar,
    get_database_engine,
    mask_database_url,
    normalize_param_for_postgres,
    sanitize_sql_for_postgres,
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


def test_parameter_converter():
    print("\n--- 1. SQL PARAMETER CONVERTER TESTS ---")

    # Simple queries
    s1 = "SELECT * FROM tickets WHERE id = ? AND shop_id = ?"
    assert convert_qmark_to_dollar(s1) == "SELECT * FROM tickets WHERE id = $1 AND shop_id = $2"
    ok("Simple two-parameter query conversion")

    # String literal containing question mark
    s2 = "SELECT * FROM tickets WHERE reported_problem LIKE '%?%' AND shop_id = ?"
    assert convert_qmark_to_dollar(s2) == "SELECT * FROM tickets WHERE reported_problem LIKE '%?%' AND shop_id = $1"
    ok("Preserves question mark inside single-quoted string literal")

    # Escaped quote inside string literal
    s3 = "INSERT INTO shops (shop_name) VALUES ('Sharma''s Repairs?')"
    assert convert_qmark_to_dollar(s3) == "INSERT INTO shops (shop_name) VALUES ('Sharma''s Repairs?')"
    ok("Preserves escaped quotes and question marks in literals")

    # Line comment containing question mark
    s4 = "SELECT id FROM shops -- is this shop active? \nWHERE username = ?"
    assert convert_qmark_to_dollar(s4) == "SELECT id FROM shops -- is this shop active? \nWHERE username = $1"
    ok("Preserves question marks inside line comments")

    # Block comment containing question mark
    s5 = "SELECT /* does this exist? */ id, name FROM customers WHERE shop_id = ? AND phone = ?"
    assert convert_qmark_to_dollar(s5) == "SELECT /* does this exist? */ id, name FROM customers WHERE shop_id = $1 AND phone = $2"
    ok("Preserves question marks inside block comments")

    # Multiple parameters in INSERT statement
    s6 = "INSERT INTO customers (shop_id, name, phone, email) VALUES (?, ?, ?, ?)"
    assert convert_qmark_to_dollar(s6) == "INSERT INTO customers (shop_id, name, phone, email) VALUES ($1, $2, $3, $4)"
    ok("Multi-parameter INSERT conversion")


def test_row_wrapper():
    print("\n--- 2. ROW WRAPPER TESTS ---")

    now = datetime.now(timezone.utc)
    raw_data = {
        "id": 1,
        "username": "sharma",
        "created_at": now,
        "estimated_cost": Decimal("450.50"),
        "shop_name": "Sharma Electronics",
    }
    row = RowWrapper(raw_data)

    # Dictionary conversion
    d = dict(row)
    assert d["id"] == 1
    assert d["username"] == "sharma"
    assert isinstance(d["created_at"], str)  # Serialized to ISO string
    assert isinstance(d["estimated_cost"], float)  # Converted from Decimal to float
    assert d["estimated_cost"] == 450.50
    ok("RowWrapper dict() conversion with datetime serialization and Decimal->float conversion")

    # Key access and index access
    assert row["username"] == "sharma"
    assert row[0] == 1  # Index access
    assert row.get("missing_key", "default_val") == "default_val"
    ok("RowWrapper key and index access")

    # Mapping protocol
    assert len(row) == 5
    assert "shop_name" in row
    ok("RowWrapper Mapping protocol compliance")


def test_parameter_normalization():
    print("\n--- 2.1 PARAMETER NORMALIZATION TESTS ---")

    iso_str = "2026-11-09T10:10:36.987539+00:00"
    normalized = normalize_param_for_postgres(iso_str)
    assert isinstance(normalized, datetime)
    assert normalized.year == 2026 and normalized.month == 11 and normalized.day == 9
    ok("normalize_param_for_postgres correctly converts ISO string to datetime")

    plain_str = "Just a regular customer note"
    assert normalize_param_for_postgres(plain_str) == plain_str
    ok("normalize_param_for_postgres preserves standard text strings")

    int_val = 42
    assert normalize_param_for_postgres(int_val) == int_val
    ok("normalize_param_for_postgres preserves integer types")

    float_val = 450.50
    norm_float = normalize_param_for_postgres(float_val)
    assert isinstance(norm_float, Decimal)
    assert norm_float == Decimal("450.5")
    ok("normalize_param_for_postgres converts float to Decimal for NUMERIC columns")


def test_sql_sanitizer():
    print("\n--- 2.2 SQL SANITIZER TESTS ---")

    raw_sql = "SELECT id FROM shops WHERE username = ? COLLATE NOCASE"
    sanitized = sanitize_sql_for_postgres(raw_sql)
    assert "LOWER(username) = LOWER(?)" in sanitized
    assert "COLLATE NOCASE" not in sanitized
    ok("sanitize_sql_for_postgres converts 'username = ? COLLATE NOCASE' to LOWER()")


def test_url_masking_and_engine():
    print("\n--- 3. ENGINE SELECTION & URL MASKING ---")

    # URL Masking
    secret_url = "postgresql://myuser:SuperSecretPassword123@ep-example-endpoint.us-east-2.aws.neon.tech/neondb?sslmode=require"
    masked = mask_database_url(secret_url)
    assert "SuperSecretPassword123" not in masked
    assert "myuser:***@ep-example-endpoint.us-east-2.aws.neon.tech" in masked
    ok("mask_database_url successfully redacts sensitive password")

    # Engine detection
    os.environ.pop("DATABASE_URL", None)
    assert get_database_engine() == "sqlite"
    ok("get_database_engine defaults to 'sqlite' when DATABASE_URL is unset")

    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
    assert get_database_engine() == "postgres"
    ok("get_database_engine returns 'postgres' when postgresql:// is configured")

    os.environ["DATABASE_URL"] = "postgres://user:pass@localhost/db"
    assert get_database_engine() == "postgres"
    ok("get_database_engine returns 'postgres' when postgres:// is configured")

    os.environ.pop("DATABASE_URL", None)


async def test_sqlite_wrapper_async():
    print("\n--- 4. SQLITE WRAPPER ASYNC INTEGRATION ---")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        async with aiosqlite.connect(tmp_path) as raw_conn:
            raw_conn.row_factory = aiosqlite.Row
            wrapper = SqliteConnectionWrapper(raw_conn)

            # Create table
            await wrapper.execute(
                """
                CREATE TABLE test_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL
                )
                """
            )
            await wrapper.commit()
            ok("SqliteConnectionWrapper CREATE TABLE executed and committed")

            # INSERT and verify lastrowid
            cur = await wrapper.execute(
                "INSERT INTO test_items (name, value) VALUES (?, ?)",
                ("Item Alpha", 49.99),
            )
            await wrapper.commit()
            assert cur.lastrowid == 1, f"Expected lastrowid=1, got {cur.lastrowid}"
            ok(f"SqliteConnectionWrapper INSERT captured lastrowid = {cur.lastrowid}")

            # Second INSERT
            cur2 = await wrapper.execute(
                "INSERT INTO test_items (name, value) VALUES (?, ?)",
                ("Item Beta", 99.50),
            )
            await wrapper.commit()
            assert cur2.lastrowid == 2
            ok(f"SqliteConnectionWrapper second INSERT captured lastrowid = {cur2.lastrowid}")

            # SELECT fetchone
            cur_sel = await wrapper.execute("SELECT * FROM test_items WHERE id = ?", (1,))
            row = await cur_sel.fetchone()
            assert row is not None
            assert row["name"] == "Item Alpha"
            assert row[1] == "Item Alpha"
            assert dict(row)["value"] == 49.99
            ok("SqliteConnectionWrapper fetchone() returned valid RowWrapper")

            # SELECT fetchall
            cur_all = await wrapper.execute("SELECT * FROM test_items ORDER BY id")
            rows = await cur_all.fetchall()
            assert len(rows) == 2
            assert rows[1]["name"] == "Item Beta"
            ok(f"SqliteConnectionWrapper fetchall() returned {len(rows)} RowWrappers")

    finally:
        tmp_path.unlink(missing_ok=True)


async def test_postgres_wrapper_mock():
    print("\n--- 5. POSTGRES WRAPPER LOGIC & RETURNING ID ---")

    # Create a mock asyncpg connection to test SQL rewriting, execution flow and RETURNING id injection
    class MockAsyncpgConnection:
        def __init__(self):
            self.executed_queries = []
            self.executed_params = []
            self.next_id = 100

        async def fetch(self, sql, *params):
            self.executed_queries.append(sql)
            self.executed_params.append(params)
            # If query is INSERT ... RETURNING id
            if "RETURNING id" in sql:
                self.next_id += 1
                return [{"id": self.next_id}]
            # If query is SELECT
            if sql.startswith("SELECT"):
                return [
                    {"id": 1, "username": "sharma", "shop_name": "Sharma Electronics"},
                    {"id": 2, "username": "testshop", "shop_name": "Test Electronics"},
                ]
            return []

        async def execute(self, sql, *params):
            self.executed_queries.append(sql)
            self.executed_params.append(params)
            if sql.startswith("UPDATE") or sql.startswith("DELETE"):
                return "UPDATE 1"
            if sql.startswith("INSERT"):
                return "INSERT 0 1"
            return "SUCCESS"

        def transaction(self):
            class MockTransaction:
                async def start(self): pass
                async def commit(self): pass
                async def rollback(self): pass
            return MockTransaction()

    mock_conn = MockAsyncpgConnection()
    pg_wrapper = PostgresConnectionWrapper(mock_conn)

    # 1. Test INSERT without RETURNING appends RETURNING id for tables with id
    insert_sql = "INSERT INTO shops (username, password_hash, shop_name) VALUES (?, ?, ?)"
    params = ("newshop", "hash123", "New Shop")
    cur = await pg_wrapper.execute(insert_sql, params)

    assert "RETURNING id;" in mock_conn.executed_queries[0]
    assert "$1, $2, $3" in mock_conn.executed_queries[0]
    assert cur.lastrowid == 101, f"Expected lastrowid=101, got {cur.lastrowid}"
    ok("PostgresConnectionWrapper automatically appends RETURNING id and populates lastrowid for shops")

    # 1.1 Test INSERT into sessions does NOT append RETURNING id (sessions PK is token)
    session_insert_sql = "INSERT INTO sessions (token, shop_id, created_at, expires_at) VALUES (?, ?, ?, ?)"
    session_params = ("tok_abc123", 1, "2026-01-01T00:00:00Z", "2026-01-08T00:00:00Z")
    cur_sess = await pg_wrapper.execute(session_insert_sql, session_params)
    assert "RETURNING" not in mock_conn.executed_queries[1], "sessions insert must not append RETURNING id"
    assert "$1, $2, $3, $4" in mock_conn.executed_queries[1]
    assert cur_sess.lastrowid is None
    ok("PostgresConnectionWrapper correctly avoids RETURNING id for sessions table")

    # 1.2 Test create_session from auth service with PostgresConnectionWrapper
    from backend.services.auth import create_session
    generated_token = await create_session(pg_wrapper, shop_id=1)
    assert isinstance(generated_token, str) and len(generated_token) > 20
    assert "RETURNING" not in mock_conn.executed_queries[-1]
    ok("create_session executes cleanly against PostgresConnectionWrapper without UndefinedColumnError")

    # 2. Test SELECT parameter conversion
    select_sql = "SELECT * FROM tickets WHERE id = ? AND shop_id = ?"
    cur2 = await pg_wrapper.execute(select_sql, (1, 1))
    assert mock_conn.executed_queries[3] == "SELECT * FROM tickets WHERE id = $1 AND shop_id = $2"
    rows = await cur2.fetchall()
    assert len(rows) == 2
    assert rows[0]["username"] == "sharma"
    ok("PostgresConnectionWrapper correctly executed SELECT with $1, $2 and returned RowWrappers")

    # 3. Test UPDATE rowcount parsing
    update_sql = "UPDATE tickets SET status = ? WHERE id = ? AND shop_id = ?"
    cur3 = await pg_wrapper.execute(update_sql, ("in_progress", 1, 1))
    assert cur3.rowcount == 1
    ok("PostgresConnectionWrapper parsed UPDATE command tag into rowcount = 1")

    # 4. Test Customer Listing Query (GROUP BY c.id)
    cust_list_sql = """
        SELECT c.id, c.shop_id, c.name, c.phone, c.alternate_phone, c.email, c.notes,
               c.created_at, c.updated_at,
               COUNT(t.id) AS total_tickets
        FROM customers c
        LEFT JOIN tickets t ON t.customer_id = c.id
        WHERE c.shop_id = ?
        GROUP BY c.id ORDER BY c.updated_at DESC
    """
    cur4 = await pg_wrapper.execute(cust_list_sql, (1,))
    assert "$1" in mock_conn.executed_queries[5]
    ok("Customer listing query converted parameters correctly for PostgreSQL")

    # 5. Test Session Expiry Query with ISO Timestamp parameter
    session_sql = """
        SELECT s.id, s.username, s.shop_name, s.owner_name, s.phone, s.branch, s.address, s.created_at
        FROM sessions sess
        JOIN shops s ON sess.shop_id = s.id
        WHERE sess.token = ? AND sess.expires_at > ?
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    cur5 = await pg_wrapper.execute(session_sql, ("test-token-12345", now_iso))
    assert "$1" in mock_conn.executed_queries[6] and "$2" in mock_conn.executed_queries[6]
    # Verify the normalized parameter is a real datetime object, not a raw string
    assert isinstance(mock_conn.executed_params[6][1], datetime)
    ok("Session token query converted ISO string parameter to datetime for TIMESTAMPTZ comparison")

    # 6. Test Speech Confirmation Query
    speech_sql = "SELECT * FROM tickets WHERE id = ? AND shop_id = ?"
    cur6 = await pg_wrapper.execute(speech_sql, (1, 1))
    assert "$1" in mock_conn.executed_queries[7] and "$2" in mock_conn.executed_queries[7]
    ok("Speech confirmation query successfully converted for PostgreSQL")


def main():
    print("=" * 60)
    print("  BOLTI SLIP DATABASE ADAPTER TEST SUITE")
    print("=" * 60)

    test_parameter_converter()
    test_row_wrapper()
    test_parameter_normalization()
    test_sql_sanitizer()
    test_url_masking_and_engine()
    asyncio.run(test_sqlite_wrapper_async())
    asyncio.run(test_postgres_wrapper_mock())

    print("\n" + "=" * 60)
    print(f"  SUMMARY: PASSED {PASS} | FAILED {FAIL}")
    print("=" * 60)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
