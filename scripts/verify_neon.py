"""
scripts/verify_neon.py
----------------------
Read-only inspection and verification of live Neon PostgreSQL database.
Never executes INSERT, UPDATE, DELETE, or DDL.
Never prints passwords, hashes, connection strings, or raw tokens.
"""

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)

db_url = os.getenv("DATABASE_URL")
if not db_url or not (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
    print("ERROR: A valid PostgreSQL connection URL is required in root .env (DATABASE_URL).")
    sys.exit(1)

clean_dsn = db_url.split("?")[0] if "?" in db_url else db_url
ssl_val = "require" if ("neon.tech" in db_url or "sslmode=require" in db_url) else None


async def run_verification():
    conn = await asyncpg.connect(clean_dsn, ssl=ssl_val)
    try:
        print("STATUS: CONNECTED_TO_NEON_SUCCESS")

        # 1. Schema / Tables
        tables_rows = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name IN ('shops', 'customers', 'tickets', 'sessions')
            ORDER BY table_name;
        """)
        tables = [r["table_name"] for r in tables_rows]
        print("TABLES:", tables)

        # 2. Indexes
        indexes_rows = await conn.fetch("""
            SELECT tablename, indexname FROM pg_indexes
            WHERE schemaname = 'public' AND tablename IN ('shops', 'customers', 'tickets', 'sessions')
            ORDER BY tablename, indexname;
        """)
        indexes = [(r["tablename"], r["indexname"]) for r in indexes_rows]
        print("INDEXES_FOUND:", indexes)

        # 3. Triggers & Trigger Functions
        triggers_rows = await conn.fetch("""
            SELECT trigger_name, event_object_table, action_timing, event_manipulation
            FROM information_schema.triggers
            WHERE trigger_schema = 'public'
            ORDER BY event_object_table, trigger_name;
        """)
        triggers = [(r["event_object_table"], r["trigger_name"]) for r in triggers_rows]
        print("TRIGGERS:", triggers)

        # 4. Record counts
        shops_cnt = await conn.fetchval("SELECT count(*) FROM shops;")
        cust_cnt = await conn.fetchval("SELECT count(*) FROM customers;")
        tix_cnt = await conn.fetchval("SELECT count(*) FROM tickets;")
        sess_cnt = await conn.fetchval("SELECT count(*) FROM sessions;")
        print("COUNTS:", {"shops": shops_cnt, "customers": cust_cnt, "tickets": tix_cnt, "sessions": sess_cnt})

        # 5. Sequences state
        sequences_rows = await conn.fetch("""
            SELECT sequencename, last_value, start_value, min_value, max_value, increment_by
            FROM pg_sequences WHERE schemaname = 'public'
            ORDER BY sequencename;
        """)
        print("SEQUENCES:", [dict(r) for r in sequences_rows])

        # 6. Foreign-key & Relationship integrity
        orphaned_cust = await conn.fetchval("SELECT count(*) FROM customers WHERE shop_id NOT IN (SELECT id FROM shops);")
        orphaned_tix_shop = await conn.fetchval("SELECT count(*) FROM tickets WHERE shop_id IS NOT NULL AND shop_id NOT IN (SELECT id FROM shops);")
        orphaned_tix_cust = await conn.fetchval("SELECT count(*) FROM tickets WHERE customer_id IS NOT NULL AND customer_id NOT IN (SELECT id FROM customers);")
        orphaned_sess = await conn.fetchval("SELECT count(*) FROM sessions WHERE shop_id NOT IN (SELECT id FROM shops);")
        print("FOREIGN_KEY_INTEGRITY:", {
            "orphaned_customers": orphaned_cust,
            "orphaned_tickets_shop": orphaned_tix_shop,
            "orphaned_tickets_customer": orphaned_tix_cust,
            "orphaned_sessions": orphaned_sess,
        })

        # 7. Shops inspection (no password hashes)
        shops_rows = await conn.fetch("SELECT id, username, shop_name, owner_name, phone, branch FROM shops ORDER BY id;")
        print("SHOPS_LIST:", [dict(r) for r in shops_rows])

        # 8. Customers inspection
        cust_rows = await conn.fetch("SELECT id, shop_id, name, phone, alternate_phone, email FROM customers ORDER BY id;")
        print("CUSTOMERS_LIST:", [dict(r) for r in cust_rows])

        # 9. Tickets inspection with estimated_cost readability
        tix_rows = await conn.fetch("""
            SELECT id, ticket_number, shop_id, customer_id, customer_name, customer_phone,
                   device_description, status, estimated_cost
            FROM tickets ORDER BY id;
        """)
        tix_data = []
        for r in tix_rows:
            d = dict(r)
            cost_val = d["estimated_cost"]
            cost_type = type(cost_val).__name__ if cost_val is not None else "None"
            d["estimated_cost_str"] = str(cost_val) if cost_val is not None else None
            d["estimated_cost_type"] = cost_type
            del d["estimated_cost"]
            tix_data.append(d)
        print("TICKETS_LIST:", tix_data)

        # 10. Sessions summary (no tokens)
        sess_rows = await conn.fetch("""
            SELECT shop_id, count(*) as count, min(created_at) as earliest, max(expires_at) as latest
            FROM sessions GROUP BY shop_id ORDER BY shop_id;
        """)
        print("SESSIONS_BY_SHOP:", [dict(r) for r in sess_rows])

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_verification())
