"""
backend/database/db.py
----------------------
Async SQLite connection pool using aiosqlite.

Provides:
- get_db()   — FastAPI dependency that yields a live connection per request
- init_db()  — called once at startup to create tables via migration scripts
"""

import sqlite3
import aiosqlite
from pathlib import Path

# Database file lives at the project root (one level above backend/)
_DB_PATH        = Path(__file__).parent.parent.parent / "bolti_slip.db"
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def sync_init_db() -> None:
    """
    Run all migration scripts in order using synchronous sqlite3.

    001_create_tickets.sql    — initial schema (idempotent via IF NOT EXISTS)
    002_add_ticket_fields.sql — four new columns; each ALTER TABLE is guarded
                                by a column-existence check so re-runs are safe.
    """
    with sqlite3.connect(_DB_PATH) as conn:
        # --- Migration 001: base schema ---
        sql_001 = (_MIGRATIONS_DIR / "001_create_tickets.sql").read_text(encoding="utf-8")
        conn.executescript(sql_001)

        # --- Migration 002: additional ticket fields ---
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tickets)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        new_columns = [
            ("reported_problem",    "TEXT"),
            ("repair_instructions", "TEXT"),
            ("expected_delivery",   "TEXT"),
            ("estimated_cost",      "REAL"),
        ]
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                conn.execute(f"ALTER TABLE tickets ADD COLUMN {col_name} {col_type}")
        conn.commit()


async def init_db() -> None:
    """FastAPI lifespan wrapper for sync_init_db."""
    sync_init_db()


async def get_db():
    """
    FastAPI dependency — yields an open aiosqlite connection with
    row_factory set so rows behave like dicts.
    """
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
