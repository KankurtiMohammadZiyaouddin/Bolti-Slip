"""
scripts/test_postgres_session_login.py
----------------------------------------
Targeted regression tests for PostgreSQL session creation and login flow.
Specifically verifies that 'INSERT INTO sessions' does NOT append 'RETURNING id'
(which caused UndefinedColumnError: column "id" does not exist in production).

Safety:
- Distinguishes MOCK tests from REAL PostgreSQL integration tests.
- Real PostgreSQL test uses an atomic transaction that is ALWAYS rolled back.
- Zero modifications to production data.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from backend.database.adapter import PostgresConnectionWrapper, RowWrapper
from backend.services.auth import (
    create_session,
    get_shop_by_token,
    delete_session,
    revoke_other_sessions,
    hash_password,
    verify_password,
)

PASS = 0
FAIL = 0


def ok(msg: str):
    global PASS
    PASS += 1
    print(f"  [PASS] {msg}")


def fail(msg: str, reason: str = ""):
    global FAIL
    FAIL += 1
    err = f" -- {reason}" if reason else ""
    print(f"  [FAIL] {msg}{err}")


# ---------------------------------------------------------------------------
# 1. MOCK ASYNCPG SESSION LIFECYCLE TESTS
# ---------------------------------------------------------------------------
async def test_mock_postgres_session_lifecycle():
    print("\n--- 1. MOCK ASYNCPG SESSION & LOGIN TESTS ---")

    class MockAsyncpgSessionConn:
        def __init__(self):
            self.queries = []
            self.params = []
            self.sessions_table = {}

        async def execute(self, sql, *params):
            self.queries.append(sql)
            self.params.append(params)
            if "INSERT INTO sessions" in sql:
                token, shop_id, created_at, expires_at = params
                self.sessions_table[token] = {
                    "token": token,
                    "shop_id": shop_id,
                    "created_at": created_at,
                    "expires_at": expires_at,
                }
                return "INSERT 0 1"
            elif "DELETE FROM sessions" in sql:
                return "DELETE 1"
            return "SUCCESS"

        async def fetch(self, sql, *params):
            self.queries.append(sql)
            self.params.append(params)
            if "FROM sessions" in sql and "JOIN shops" in sql:
                token = params[0]
                if token in self.sessions_table:
                    s = self.sessions_table[token]
                    return [
                        {
                            "id": s["shop_id"],
                            "username": "sharma",
                            "shop_name": "Sharma Electronics",
                            "owner_name": "Rajesh Sharma",
                            "phone": "9876543210",
                            "branch": "Main Branch",
                            "address": "Pune",
                            "created_at": datetime.now(timezone.utc),
                        }
                    ]
                return []
            return []

        async def fetchrow(self, sql, *params):
            rows = await self.fetch(sql, *params)
            return rows[0] if rows else None

        def transaction(self):
            class DummyTr:
                async def start(self): pass
                async def commit(self): pass
                async def rollback(self): pass
            return DummyTr()

    mock_conn = MockAsyncpgSessionConn()
    wrapper = PostgresConnectionWrapper(mock_conn)

    # Test A: create_session generates valid token without RETURNING id
    token = await create_session(wrapper, shop_id=1, days=30)
    assert isinstance(token, str) and len(token) >= 32
    assert "RETURNING" not in mock_conn.queries[0]
    assert "INSERT INTO sessions" in mock_conn.queries[0]
    assert "$1, $2, $3, $4" in mock_conn.queries[0]
    ok("[MOCK] create_session successfully inserted session without 'RETURNING id'")

    # Test B: Token can be retrieved via get_shop_by_token
    shop = await get_shop_by_token(wrapper, token)
    assert shop is not None
    assert shop["username"] == "sharma"
    ok("[MOCK] get_shop_by_token successfully retrieved shop with session token")

    # Test C: delete_session successfully deletes token
    deleted = await delete_session(wrapper, token)
    assert deleted is True
    ok("[MOCK] delete_session executed successfully against PostgresConnectionWrapper")

    # Test D: revoke_other_sessions executes cleanly
    revoked = await revoke_other_sessions(wrapper, shop_id=1, keep_token=token)
    assert revoked >= 0
    ok("[MOCK] revoke_other_sessions executed cleanly against PostgresConnectionWrapper")


# ---------------------------------------------------------------------------
# 2. REAL POSTGRESQL (NEON) INTEGRATION TEST (DISABLED BY DEFAULT)
# ---------------------------------------------------------------------------
async def test_real_neon_postgres_session_lifecycle():
    print("\n--- 2. REAL NEON POSTGRESQL INTEGRATION TEST (DISABLED BY DEFAULT) ---")

    # Guard: Require explicit opt-in environment variable
    run_live = os.getenv("RUN_NEON_INTEGRATION_TESTS", "").strip().lower() in ("true", "1", "yes")
    if not run_live:
        print("  [SKIP] Real Neon integration test skipped by default.")
        print("         To enable: set RUN_NEON_INTEGRATION_TESTS=true")
        return

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    db_url = os.getenv("DATABASE_URL")
    if not db_url or not (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
        print("  [SKIP] Real Neon integration test skipped: DATABASE_URL not set.")
        return

    import asyncpg
    clean_dsn = db_url.split("?")[0] if "?" in db_url else db_url
    ssl_val = "require" if ("neon.tech" in db_url or "sslmode=require" in db_url) else None

    try:
        raw_conn = await asyncpg.connect(clean_dsn, ssl=ssl_val)
    except Exception as e:
        print("  [SKIP] Could not connect to real PostgreSQL server.")
        return

    try:
        # Check pre-test session count
        pre_count = await raw_conn.fetchval("SELECT COUNT(*) FROM sessions")

        # Start an isolated transaction on real Neon connection
        tr = raw_conn.transaction()
        await tr.start()

        try:
            wrapper = PostgresConnectionWrapper(raw_conn)

            # Test real INSERT INTO sessions through PostgresConnectionWrapper
            # This directly exercises the exact line that failed in Render production!
            test_token = await create_session(wrapper, shop_id=1, days=1)
            assert isinstance(test_token, str) and len(test_token) >= 32
            ok("[REAL NEON] create_session successfully inserted session into live Neon schema without UndefinedColumnError")

            # Verify session row exists inside the active transaction
            sess_row = await raw_conn.fetchrow("SELECT token, shop_id FROM sessions WHERE token = $1", test_token)
            assert sess_row is not None and sess_row["shop_id"] == 1
            ok("[REAL NEON] Session verified present in live Neon schema during transaction")

            # Test get_shop_by_token through wrapper
            shop_data = await get_shop_by_token(wrapper, test_token)
            assert shop_data is not None and shop_data["id"] == 1
            ok("[REAL NEON] get_shop_by_token successfully validated session against live Neon shops")

        finally:
            # CRITICAL SAFETY: Always rollback even if an assertion or query fails!
            # Never commit test sessions to production Neon.
            await tr.rollback()
            ok("[REAL NEON] Mandatory transaction rollback executed: zero records committed")

        # Verify post-test session count is identical
        post_count = await raw_conn.fetchval("SELECT COUNT(*) FROM sessions")
        assert post_count == pre_count, f"Pre-count {pre_count} != Post-count {post_count}"
        ok(f"[REAL NEON] Live session count verified unchanged ({post_count} sessions)")

    finally:
        await raw_conn.close()


async def main():
    print("=" * 60)
    print("  POSTGRESQL SESSION & LOGIN REGRESSION SUITE")
    print("=" * 60)

    await test_mock_postgres_session_lifecycle()
    await test_real_neon_postgres_session_lifecycle()

    print("\n" + "=" * 60)
    print(f"  SUMMARY: PASSED {PASS} | FAILED {FAIL}")
    print("=" * 60)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
