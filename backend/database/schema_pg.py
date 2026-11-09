"""
backend/database/schema_pg.py
-----------------------------
PostgreSQL schema migration runner and validator for Bolti Slip.
Executes idempotent DDL migrations located in backend/database/migrations_pg/.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

MIGRATIONS_PG_DIR = Path(__file__).resolve().parent / "migrations_pg"


async def run_postgres_migrations(conn: Any) -> List[str]:
    """
    Execute all PostgreSQL migration SQL files in alphabetical order.
    All statements are written with IF NOT EXISTS / CREATE OR REPLACE / DROP TRIGGER IF EXISTS
    so running repeatedly is completely idempotent.
    """
    if not MIGRATIONS_PG_DIR.exists():
        logger.warning("PostgreSQL migrations directory not found at: %s", MIGRATIONS_PG_DIR)
        return []

    migration_files = sorted(MIGRATIONS_PG_DIR.glob("*.sql"))
    executed: List[str] = []

    for sql_file in migration_files:
        logger.info("Executing PostgreSQL migration: %s", sql_file.name)
        sql_content = sql_file.read_text(encoding="utf-8")
        # asyncpg execute supports multiple statements in a single script
        await conn.execute(sql_content)
        executed.append(sql_file.name)

    return executed


async def verify_postgres_schema(conn: Any) -> Dict[str, Any]:
    """
    Inspect information_schema to verify that all required tables and columns exist.
    """
    expected_tables = ["shops", "customers", "tickets", "sessions"]

    rows = await conn.fetch(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = ANY($1)
        """,
        expected_tables,
    )

    found_tables = {r["table_name"] for r in rows}
    missing_tables = [t for t in expected_tables if t not in found_tables]

    # Verify updated_at trigger function
    func_row = await conn.fetchrow(
        """
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
          AND routine_name = 'update_updated_at_column'
        """
    )

    return {
        "all_tables_present": len(missing_tables) == 0,
        "found_tables": sorted(list(found_tables)),
        "missing_tables": missing_tables,
        "trigger_function_present": func_row is not None,
    }
