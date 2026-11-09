"""
scripts/migrate_sqlite_to_pg.py
--------------------------------
Safe, transactional, idempotent SQLite-to-PostgreSQL data migration tool for Bolti Slip.

Transfers all records in strict foreign-key dependency order:
  1. shops
  2. customers
  3. tickets
  4. sessions

Safety Rules:
- Opens SQLite in READ-ONLY mode. Never alters or deletes the SQLite database.
- Connects to PostgreSQL using DATABASE_URL (or --pg-url argument).
- Masks database credentials in all logs and outputs.
- Strictly detects conflicts (mismatched existing records) and halts with a clear error report.
- Idempotently skips already-migrated identical records.
- Resets PostgreSQL BIGSERIAL sequences to COALESCE(MAX(id), 1) post-insertion.
- Supports --dry-run mode: performs all checks and rollbacks transaction without committing.
- Must be explicitly invoked from CLI. Never runs automatically at application startup.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_environment(root_dir: Optional[Path] = None) -> None:
    """
    Load root project's .env file reliably using project root path with override=False.
    Existing environment variables take precedence.
    """
    target_root = root_dir or PROJECT_ROOT
    env_file = target_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)


# Load environment on module import
load_environment()

from backend.database.adapter import mask_database_url
from backend.database.schema_pg import run_postgres_migrations, verify_postgres_schema

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bolti_migrator")


class MigrationConflictError(Exception):
    """Raised when destination PostgreSQL database has conflicting records with different values."""
    pass


def parse_iso_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 string from SQLite into timezone-aware datetime."""
    if not ts_str:
        return None
    try:
        # Handles 2026-11-08T16:31:52.591Z or with offsets
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def read_sqlite_data(sqlite_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Read all records from SQLite in read-only URI mode.
    Guarantees no modifications to the SQLite database.
    """
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found at: {sqlite_path}")

    # Open with read-only URI
    uri = f"file:{sqlite_path.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    data: Dict[str, List[Dict[str, Any]]] = {}

    try:
        # 1. Shops
        shops_rows = c.execute("SELECT * FROM shops ORDER BY id ASC").fetchall()
        data["shops"] = [dict(r) for r in shops_rows]

        # 2. Customers
        customers_rows = c.execute("SELECT * FROM customers ORDER BY id ASC").fetchall()
        data["customers"] = [dict(r) for r in customers_rows]

        # 3. Tickets
        tickets_rows = c.execute("SELECT * FROM tickets ORDER BY id ASC").fetchall()
        data["tickets"] = [dict(r) for r in tickets_rows]

        # 4. Sessions
        sessions_rows = c.execute("SELECT * FROM sessions ORDER BY shop_id ASC, created_at ASC").fetchall()
        data["sessions"] = [dict(r) for r in sessions_rows]

    finally:
        conn.close()

    return data


async def migrate_data(
    sqlite_path: Path,
    pg_dsn: str,
    dry_run: bool = False,
    auto_init_schema: bool = True,
) -> Dict[str, Any]:
    """
    Migrate SQLite data to PostgreSQL within a single atomic transaction.
    """
    import asyncpg

    logger.info("Reading source data from SQLite: %s", sqlite_path.name)
    src = read_sqlite_data(sqlite_path)

    logger.info("Source records found: %d shops, %d customers, %d tickets, %d sessions",
                len(src["shops"]), len(src["customers"]), len(src["tickets"]), len(src["sessions"]))

    masked_url = mask_database_url(pg_dsn)
    logger.info("Connecting to target PostgreSQL: %s", masked_url)

    clean_dsn = pg_dsn.split("?")[0] if "?" in pg_dsn else pg_dsn
    ssl_val = "require" if ("neon.tech" in pg_dsn or "sslmode=require" in pg_dsn) else None

    conn = await asyncpg.connect(clean_dsn, ssl=ssl_val)

    stats = {
        "shops_inserted": 0,
        "shops_already_migrated": 0,
        "customers_inserted": 0,
        "customers_already_migrated": 0,
        "tickets_inserted": 0,
        "tickets_already_migrated": 0,
        "sessions_inserted": 0,
        "sessions_already_migrated": 0,
    }

    try:
        # Start atomic transaction (wraps both schema migrations and data transfers)
        async with conn.transaction():
            logger.info("Started atomic PostgreSQL transaction...")

            if auto_init_schema:
                logger.info("Verifying/applying PostgreSQL schema migrations inside transaction...")
                await run_postgres_migrations(conn)

            schema_status = await verify_postgres_schema(conn)
            if not schema_status["all_tables_present"]:
                raise RuntimeError(f"Missing required PostgreSQL tables: {schema_status['missing_tables']}")

            # -----------------------------------------------------------------
            # 1. MIGRATE SHOPS
            # -----------------------------------------------------------------
            for shop in src["shops"]:
                s_id = shop["id"]
                s_user = shop["username"].strip().lower()
                s_hash = shop["password_hash"]
                s_name = shop["shop_name"]
                s_owner = shop["owner_name"]
                s_phone = shop.get("phone")
                s_branch = shop.get("branch") or "Main Branch"
                s_addr = shop.get("address")
                s_created = parse_iso_timestamp(shop.get("created_at"))
                s_updated = parse_iso_timestamp(shop.get("updated_at"))

                # Conflict detection: check existing record by ID or username
                existing = await conn.fetchrow(
                    "SELECT id, username, password_hash, shop_name FROM shops WHERE id = $1 OR LOWER(username) = $2",
                    s_id, s_user
                )
                if existing:
                    if (existing["id"] == s_id and
                        existing["username"].lower() == s_user and
                        existing["password_hash"] == s_hash and
                        existing["shop_name"] == s_name):
                        # Identical record already present
                        stats["shops_already_migrated"] += 1
                        continue
                    else:
                        raise MigrationConflictError(
                            f"Conflict on shop ID={s_id}, user='{s_user}'. "
                            f"Target PostgreSQL has ID={existing['id']}, user='{existing['username']}'."
                        )

                # Insert shop
                await conn.execute(
                    """
                    INSERT INTO shops (id, username, password_hash, shop_name, owner_name, phone, branch, address, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    s_id, s_user, s_hash, s_name, s_owner, s_phone, s_branch, s_addr, s_created, s_updated
                )
                stats["shops_inserted"] += 1

            # -----------------------------------------------------------------
            # 2. MIGRATE CUSTOMERS
            # -----------------------------------------------------------------
            for cust in src["customers"]:
                c_id = cust["id"]
                c_shop = cust["shop_id"]
                c_name = cust["name"]
                c_phone = cust["phone"]
                c_alt = cust.get("alternate_phone")
                c_email = cust.get("email")
                c_notes = cust.get("notes")
                c_created = parse_iso_timestamp(cust.get("created_at"))
                c_updated = parse_iso_timestamp(cust.get("updated_at"))

                existing = await conn.fetchrow(
                    "SELECT id, shop_id, phone, name FROM customers WHERE id = $1 OR (shop_id = $2 AND phone = $3)",
                    c_id, c_shop, c_phone
                )
                if existing:
                    if (existing["id"] == c_id and
                        existing["shop_id"] == c_shop and
                        existing["phone"] == c_phone and
                        existing["name"] == c_name):
                        stats["customers_already_migrated"] += 1
                        continue
                    else:
                        raise MigrationConflictError(
                            f"Conflict on customer ID={c_id}, phone='{c_phone}'. "
                            f"Target PostgreSQL has ID={existing['id']}, phone='{existing['phone']}'."
                        )

                await conn.execute(
                    """
                    INSERT INTO customers (id, shop_id, name, phone, alternate_phone, email, notes, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    c_id, c_shop, c_name, c_phone, c_alt, c_email, c_notes, c_created, c_updated
                )
                stats["customers_inserted"] += 1

            # -----------------------------------------------------------------
            # 3. MIGRATE TICKETS
            # -----------------------------------------------------------------
            for ticket in src["tickets"]:
                t_id = ticket["id"]
                t_num = ticket["ticket_number"]
                t_shop = ticket.get("shop_id")
                t_cust = ticket.get("customer_id")
                t_cname = ticket.get("customer_name")
                t_cphone = ticket.get("customer_phone")
                t_desc = ticket["device_description"]
                t_raw = ticket.get("transcript_raw")
                t_status = ticket.get("status") or "open"
                t_prob = ticket.get("reported_problem")
                t_inst = ticket.get("repair_instructions")
                t_deliv = ticket.get("expected_delivery")
                t_cost_raw = ticket.get("estimated_cost")
                t_cost = Decimal(str(t_cost_raw)) if t_cost_raw is not None else None
                t_created = parse_iso_timestamp(ticket.get("created_at"))
                t_updated = parse_iso_timestamp(ticket.get("updated_at"))

                existing = await conn.fetchrow(
                    "SELECT id, ticket_number, device_description FROM tickets WHERE id = $1 OR ticket_number = $2",
                    t_id, t_num
                )
                if existing:
                    if (existing["id"] == t_id and
                        existing["ticket_number"] == t_num and
                        existing.get("device_description") == t_desc):
                        stats["tickets_already_migrated"] += 1
                        continue
                    else:
                        raise MigrationConflictError(
                            f"Conflict on ticket ID={t_id}, number='{t_num}'. "
                            f"Target PostgreSQL has ID={existing['id']}, number='{existing['ticket_number']}'."
                        )

                await conn.execute(
                    """
                    INSERT INTO tickets (id, ticket_number, shop_id, customer_id, customer_name, customer_phone,
                                         device_description, transcript_raw, status, reported_problem,
                                         repair_instructions, expected_delivery, estimated_cost, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    """,
                    t_id, t_num, t_shop, t_cust, t_cname, t_cphone, t_desc, t_raw, t_status,
                    t_prob, t_inst, t_deliv, t_cost, t_created, t_updated
                )
                stats["tickets_inserted"] += 1

            # -----------------------------------------------------------------
            # 4. MIGRATE SESSIONS
            # -----------------------------------------------------------------
            for sess in src["sessions"]:
                token = sess["token"]
                s_shop = sess["shop_id"]
                s_created = parse_iso_timestamp(sess.get("created_at"))
                s_expires = parse_iso_timestamp(sess.get("expires_at"))

                existing = await conn.fetchrow(
                    "SELECT token, shop_id FROM sessions WHERE token = $1", token
                )
                if existing:
                    if existing["token"] == token and existing["shop_id"] == s_shop:
                        stats["sessions_already_migrated"] += 1
                        continue
                    else:
                        raise MigrationConflictError(
                            f"Conflict on session token '{token[:8]}...'. Target shop_id={existing['shop_id']}, source shop_id={s_shop}."
                        )

                await conn.execute(
                    """
                    INSERT INTO sessions (token, shop_id, created_at, expires_at)
                    VALUES ($1, $2, $3, $4)
                    """,
                    token, s_shop, s_created, s_expires
                )
                stats["sessions_inserted"] += 1

            # -----------------------------------------------------------------
            # 5. RESET BIGSERIAL SEQUENCES (Properly handles both empty and populated tables)
            # -----------------------------------------------------------------
            for tbl in ["shops", "customers", "tickets"]:
                await conn.execute(
                    f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE((SELECT MAX(id) FROM {tbl}), 1), (SELECT MAX(id) FROM {tbl}) IS NOT NULL);"
                )
            logger.info("Successfully reset PostgreSQL BIGSERIAL sequences to match MAX(id).")

            # -----------------------------------------------------------------
            # 6. POST-INSERTION VERIFICATION IN TRANSACTION
            # -----------------------------------------------------------------
            pg_shops_cnt = await conn.fetchval("SELECT count(*) FROM shops")
            pg_custs_cnt = await conn.fetchval("SELECT count(*) FROM customers")
            pg_tix_cnt = await conn.fetchval("SELECT count(*) FROM tickets")
            pg_sess_cnt = await conn.fetchval("SELECT count(*) FROM sessions")

            logger.info("Target PostgreSQL counts: %d shops, %d customers, %d tickets, %d sessions",
                        pg_shops_cnt, pg_custs_cnt, pg_tix_cnt, pg_sess_cnt)

            if dry_run:
                logger.info("DRY-RUN MODE ACTIVE: Rolling back transaction (data + schema changes).")
                raise _DryRunRollback()

        logger.info("TRANSACTION COMMITTED: Migration completed successfully.")

    except _DryRunRollback:
        stats["dry_run"] = True
    finally:
        await conn.close()

    return stats


class _DryRunRollback(Exception):
    """Internal sentinel used to safely rollback during dry run."""
    pass


def main():
    # Ensure root .env is loaded before creating argument parser or reading DATABASE_URL
    load_environment()

    parser = argparse.ArgumentParser(description="Bolti Slip SQLite-to-PostgreSQL Data Migration Tool")
    parser.add_argument("--sqlite-path", default=str(PROJECT_ROOT / "bolti_slip.db"), help="Path to source SQLite database")
    parser.add_argument("--pg-url", default=os.getenv("DATABASE_URL"), help="PostgreSQL connection URL (or DATABASE_URL env)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration and verify integrity without committing")
    args = parser.parse_args()

    sqlite_path = Path(args.sqlite_path)
    pg_url = args.pg_url

    if not pg_url or not (pg_url.startswith("postgresql://") or pg_url.startswith("postgres://")):
        logger.error("A valid PostgreSQL connection URL is required (via --pg-url or DATABASE_URL).")
        sys.exit(1)

    try:
        stats = asyncio.run(
            migrate_data(
                sqlite_path=sqlite_path,
                pg_dsn=pg_url,
                dry_run=args.dry_run,
            )
        )
        print("\n" + "=" * 60)
        print("  MIGRATION SUMMARY")
        print("=" * 60)
        for k, v in stats.items():
            print(f"  {k}: {v}")
        print("=" * 60)
        if args.dry_run:
            print("  DRY-RUN COMPLETE: Target PostgreSQL was not modified.")
        else:
            print("  SUCCESS: Data migrated and sequences synchronized.")
    except Exception as e:
        logger.error("Migration failed: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
