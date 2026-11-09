"""
backend/database/db.py
----------------------
Async SQLite connection pool using aiosqlite.

Provides:
- get_db()   — FastAPI dependency that yields a live connection per request
- init_db()  — called once at startup to create tables via migration scripts
"""

import logging
import os
import sqlite3
import aiosqlite
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Database file lives at the project root (one level above backend/)
_PROJECT_ROOT   = Path(__file__).resolve().parent.parent.parent
_DB_PATH        = _PROJECT_ROOT / "bolti_slip.db"
_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def sync_init_db() -> None:
    """
    Run all migration scripts in order using synchronous sqlite3.

    001_create_tickets.sql    — initial schema (idempotent via IF NOT EXISTS)
    002_add_ticket_fields.sql — four new columns; each ALTER TABLE is guarded
                                by a column-existence check so re-runs are safe.
    """
    # Load root .env and backend/.env (override=False preserves deployment environment)
    load_dotenv(_PROJECT_ROOT / ".env", override=False)
    load_dotenv(_PROJECT_ROOT / "backend" / ".env", override=False)

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

        # --- Migration 003: shops, customers, sessions & foreign keys ---
        sql_003 = (_MIGRATIONS_DIR / "003_add_auth_and_customers.sql").read_text(encoding="utf-8")
        conn.executescript(sql_003)

        cursor.execute("PRAGMA table_info(tickets)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "shop_id" not in existing_cols:
            conn.execute("ALTER TABLE tickets ADD COLUMN shop_id INTEGER REFERENCES shops(id)")
        if "customer_id" not in existing_cols:
            conn.execute("ALTER TABLE tickets ADD COLUMN customer_id INTEGER REFERENCES customers(id)")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_shop ON tickets(shop_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(customer_id)")
        conn.commit()

        # Seed default shopkeeper (Sharma Electronics) if BOLTI_SEED_PASSWORD is configured and no shops exist
        cursor.execute("SELECT COUNT(*) FROM shops")
        shop_count = cursor.fetchone()[0]
        if shop_count == 0:
            seed_password = os.getenv("BOLTI_SEED_PASSWORD")
            if seed_password and seed_password.strip():
                clean_pw = seed_password.strip()
                if 6 <= len(clean_pw) <= 128:
                    from backend.services.auth import hash_password

                    default_hash = hash_password(clean_pw)
                    try:
                        conn.execute(
                            """
                            INSERT INTO shops (id, username, password_hash, shop_name, owner_name, phone, branch, address)
                            VALUES (1, 'sharma', ?, 'Sharma Electronics', 'Rajesh Sharma', '9876543210', 'Pune Main Branch', 'Shop 4, Market Yard, Pune')
                            """,
                            (default_hash,)
                        )
                        conn.commit()
                    except sqlite3.IntegrityError as ie:
                        # Another concurrent startup process or worker already inserted the first shop
                        cursor.execute("SELECT COUNT(*) FROM shops")
                        if cursor.fetchone()[0] > 0:
                            logging.getLogger(__name__).info(
                                "First shop already created by a concurrent process during startup. Continuing."
                            )
                        else:
                            raise ie
                else:
                    logging.getLogger(__name__).warning(
                        "BOLTI_SEED_PASSWORD does not meet length requirements (6-128 chars). "
                        "Skipping seed account creation. Use web registration or CLI setup."
                    )
            # If BOLTI_SEED_PASSWORD is not set or empty, no inaccessible default account is created.
            # The first shop owner can register via web UI (/register) or CLI (scripts/setup_first_shop.py).

        # Backfill existing legacy tickets to default shop_id = 1 ONLY if shop_id = 1 exists
        cursor.execute("SELECT id FROM shops WHERE id = 1")
        if cursor.fetchone():
            conn.execute("UPDATE tickets SET shop_id = 1 WHERE shop_id IS NULL")
            conn.commit()

            # Deduplicate & backfill customers from tickets under shop_id = 1
            cursor.execute(
                """
                SELECT customer_name, customer_phone, MIN(created_at)
                FROM tickets
                WHERE customer_phone IS NOT NULL AND TRIM(customer_phone) != ''
                GROUP BY customer_phone
                """
            )
            for c_name, c_phone, c_created in cursor.fetchall():
                cursor.execute("SELECT id FROM customers WHERE shop_id = 1 AND phone = ?", (c_phone,))
                cust_row = cursor.fetchone()
                if cust_row:
                    cust_id = cust_row[0]
                else:
                    cust_name = c_name if (c_name and c_name.strip()) else "Valued Customer"
                    cur_ins = conn.execute(
                        """
                        INSERT INTO customers (shop_id, name, phone, created_at, updated_at)
                        VALUES (1, ?, ?, ?, ?)
                        """,
                        (cust_name, c_phone, c_created, c_created)
                    )
                    cust_id = cur_ins.lastrowid

                conn.execute(
                    "UPDATE tickets SET customer_id = ? WHERE shop_id = 1 AND customer_phone = ? AND customer_id IS NULL",
                    (cust_id, c_phone)
                )
            conn.commit()


async def init_db() -> None:
    """FastAPI lifespan wrapper for database schema initialization."""
    engine = get_database_engine()
    if engine == "postgres":
        from backend.database.schema_pg import run_postgres_migrations
        logger.info("Database engine: PostgreSQL. Initializing schema migrations...")
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            await run_postgres_migrations(conn)
    else:
        sync_init_db()


# Re-export backup functions for convenient external scheduling and administration
from backend.database.backup import create_backup, run_backup_retention
from backend.database.adapter import (
    get_database_engine,
    mask_database_url,
    PostgresConnectionWrapper,
    SqliteConnectionWrapper,
)

_pg_pool = None


async def get_pg_pool():
    """Lazily initialize and return the asyncpg connection pool."""
    global _pg_pool
    if _pg_pool is None:
        import asyncpg
        db_url = os.getenv("DATABASE_URL", "").strip()
        logger.info("Initializing asyncpg connection pool for PostgreSQL engine...")
        # Neon serverless endpoints require SSL (sslmode=require)
        ssl_val = "require" if ("neon.tech" in db_url or "sslmode=require" in db_url) else None
        # Clean query string parameters that asyncpg handles via explicit kwargs
        clean_dsn = db_url.split("?")[0] if "?" in db_url else db_url
        _pg_pool = await asyncpg.create_pool(
            dsn=clean_dsn,
            min_size=1,
            max_size=10,
            ssl=ssl_val,
        )
    return _pg_pool


async def close_db() -> None:
    """Close connection pools during application shutdown."""
    global _pg_pool
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None


async def get_db():
    """
    FastAPI dependency — yields a live database connection per request.
    Defaults to SQLite for local development and test isolation.
    Uses PostgreSQL (via asyncpg connection pool) when DATABASE_URL is configured.
    """
    if get_database_engine() == "postgres":
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            wrapper = PostgresConnectionWrapper(conn)
            try:
                yield wrapper
            finally:
                await wrapper.close()
    else:
        async with aiosqlite.connect(_DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            yield db
