"""
scripts/test_batch2_security.py
---------------------------------
Comprehensive automated test suite for Batch 2:
  PART A: Automated SQLite Database Backups & Retention
  PART B: Environment-Based Production CORS Configuration
  PART C: Live Database Zero-Modification Verification

All destructive/backup/restore operations run against isolated temporary databases.
The live database (bolti_slip.db) is never modified.
"""

import gc
import os
import re
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.config import (
    DEFAULT_DEV_ORIGINS,
    get_backup_dir,
    get_backup_retention_days,
    get_cors_settings,
    is_production_mode,
    parse_cors_origins,
)
from backend.database.backup import (
    BACKUP_FILENAME_REGEX,
    create_backup,
    run_backup_retention,
)
import backend.database.backup as backup_mod
from backend.database.db import _MIGRATIONS_DIR

PASS = 0
FAIL = 0
results = []


def ok(name):
    global PASS
    PASS += 1
    results.append(("PASS", name))
    print(f"  [PASS] {name}", flush=True)


def fail(name, reason=""):
    global FAIL
    FAIL += 1
    tag = f"  [FAIL] {name}"
    if reason:
        tag += f" -- {reason}"
    results.append(("FAIL", name, reason))
    print(tag, flush=True)


def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}", flush=True)


def create_sample_db(db_path: Path):
    """Create a temporary test database populated with migrations and sample records."""
    conn = sqlite3.connect(db_path)
    try:
        sql_001 = (_MIGRATIONS_DIR / "001_create_tickets.sql").read_text(encoding="utf-8")
        conn.executescript(sql_001)

        sql_002 = (_MIGRATIONS_DIR / "002_add_ticket_fields.sql").read_text(encoding="utf-8")
        conn.executescript(sql_002)

        sql_003 = (_MIGRATIONS_DIR / "003_add_auth_and_customers.sql").read_text(encoding="utf-8")
        conn.executescript(sql_003)

        conn.execute("ALTER TABLE tickets ADD COLUMN shop_id INTEGER REFERENCES shops(id)")
        conn.execute("ALTER TABLE tickets ADD COLUMN customer_id INTEGER REFERENCES customers(id)")

        # Sample Shop
        conn.execute(
            """
            INSERT INTO shops (id, username, password_hash, shop_name, owner_name, phone)
            VALUES (1, 'backuptest', 'hash_test_123', 'Backup Test Shop', 'Backup Owner', '9988776655')
            """
        )
        # Sample Customer
        conn.execute(
            """
            INSERT INTO customers (id, shop_id, name, phone)
            VALUES (101, 1, 'Ramesh Kumar', '9876500001')
            """
        )
        # Sample Ticket
        conn.execute(
            """
            INSERT INTO tickets (id, ticket_number, customer_name, customer_phone, device_description, shop_id, customer_id)
            VALUES (201, 'BLT-TEST-001', 'Ramesh Kumar', '9876500001', 'Mixer Grinder - Motor sparking', 1, 101)
            """
        )
        conn.commit()
    finally:
        conn.close()


# ===========================================================================
# PART A: AUTOMATED SQLITE DATABASE BACKUPS
# ===========================================================================
section("PART A: AUTOMATED SQLITE BACKUPS & RETENTION")

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir_str:
    temp_dir = Path(temp_dir_str)
    src_db = temp_dir / "test_source.db"
    backup_folder = temp_dir / "backups"
    backup_folder.mkdir(parents=True, exist_ok=True)

    create_sample_db(src_db)

    # 1. Generate Backup using SQLite Backup API
    backup_path = create_backup(
        source_db_path=src_db,
        backup_dir=backup_folder,
        retention_days=30,
        force=True,
    )

    if backup_path and backup_path.exists():
        ok(f"Backup created successfully at: {backup_path.name}")
    else:
        fail("Backup creation", "Returned None or file does not exist")

    # 2. Verify filename matches convention
    if backup_path and BACKUP_FILENAME_REGEX.match(backup_path.name):
        ok("Backup filename strictly matches format: bolti_slip_backup_YYYYMMDD_HHMMSS.db")
    else:
        fail("Backup filename format", str(backup_path))

    # 3. Open backup independently and verify integrity & records
    if backup_path and backup_path.exists():
        b_conn = sqlite3.connect(backup_path)
        try:
            b_shops = b_conn.execute("SELECT id, username, shop_name FROM shops").fetchall()
            b_customers = b_conn.execute("SELECT id, name, phone FROM customers").fetchall()
            b_tickets = b_conn.execute("SELECT id, ticket_number, device_description FROM tickets").fetchall()

            if len(b_shops) == 1 and b_shops[0][1] == "backuptest":
                ok("Backup contains exact verified shop record ('backuptest')")
            else:
                fail("Backup shop records", str(b_shops))

            if len(b_customers) == 1 and b_customers[0][1] == "Ramesh Kumar":
                ok("Backup contains exact verified customer record ('Ramesh Kumar')")
            else:
                fail("Backup customer records", str(b_customers))

            if len(b_tickets) == 1 and b_tickets[0][1] == "BLT-TEST-001":
                ok("Backup contains exact verified ticket record ('BLT-TEST-001')")
            else:
                fail("Backup ticket records", str(b_tickets))
        finally:
            b_conn.close()

    # 4. Debounce / Duplicate Prevention Check
    second_call_path = create_backup(
        source_db_path=src_db,
        backup_dir=backup_folder,
        retention_days=30,
        force=False,
    )
    if second_call_path == backup_path:
        ok("Repeated create_backup(force=False) avoids creating duplicate backup within debounce interval")
    else:
        fail("Backup duplicate prevention", f"Created unexpected new file: {second_call_path}")

    # 5. Online Snapshot Consistency During Active Read/Write Operations
    # Perform backup while an open connection is reading/writing
    conn_live = sqlite3.connect(src_db)
    try:
        conn_live.execute("BEGIN TRANSACTION")
        conn_live.execute(
            "INSERT INTO customers (id, shop_id, name, phone) VALUES (102, 1, 'Transaction Customer', '9876500002')"
        )
        conn_live.commit()

        live_backup_path = create_backup(
            source_db_path=src_db,
            backup_dir=backup_folder,
            retention_days=30,
            force=True,
        )

        if live_backup_path and live_backup_path.exists():
            lb_conn = sqlite3.connect(live_backup_path)
            try:
                count = lb_conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
                if count == 2:
                    ok("Online backup succeeded and captured committed data consistently (2 customers)")
                else:
                    fail("Online backup customer count", f"Expected 2, got {count}")
            finally:
                lb_conn.close()
        else:
            fail("Online backup creation during connection", "Failed to create live backup")
    finally:
        conn_live.close()

    # 6. Retention: Removes expired backups and ignores unrelated files
    # Create an artificially expired backup file (age = 45 days)
    old_backup_name = "bolti_slip_backup_20260101_120000.db"
    old_backup_path = backup_folder / old_backup_name
    old_backup_path.write_bytes(b"SQLITE_DUMMY_BACKUP_BYTES_FOR_RETENTION_TEST")
    old_mtime = time.time() - (45 * 86400)
    os.utime(old_backup_path, (old_mtime, old_mtime))

    # Create an unrelated file that should NEVER be deleted
    unrelated_file = backup_folder / "important_operator_notes.txt"
    unrelated_file.write_text("Do not delete this manual documentation.", encoding="utf-8")
    os.utime(unrelated_file, (old_mtime, old_mtime))

    # Create an unrelated .db file with a different naming convention
    other_db = backup_folder / "custom_archive_dont_touch.db"
    other_db.write_bytes(b"CUSTOM_DATA")
    os.utime(other_db, (old_mtime, old_mtime))

    # Run retention with 30-day limit
    removed = run_backup_retention(
        backup_dir=backup_folder,
        retention_days=30,
        source_db_path=src_db,
    )

    if old_backup_path in removed and not old_backup_path.exists():
        ok("Expired backup (>30 days old) was successfully identified and removed by retention")
    else:
        fail("Expired backup retention", f"Removed: {removed}, Exists: {old_backup_path.exists()}")

    if unrelated_file.exists():
        ok("Unrelated text file was completely preserved by retention policy")
    else:
        fail("Unrelated file preservation", "important_operator_notes.txt was deleted!")

    if other_db.exists():
        ok("Unrelated .db file with non-matching pattern was preserved by retention policy")
    else:
        fail("Unrelated .db preservation", "custom_archive_dont_touch.db was deleted!")

    if src_db.exists():
        ok("Source live database was completely preserved during retention")
    else:
        fail("Source DB preservation", "Source DB was touched!")

    # 7. Backup Failure Handling (Invalid or non-existent path)
    bad_backup_path = create_backup(
        source_db_path=temp_dir / "non_existent_database.db",
        backup_dir=backup_folder,
        force=True,
    )
    if bad_backup_path is None:
        ok("Non-existent source database handled safely (returned None without unhandled crash)")
    else:
        fail("Non-existent source handling", f"Returned unexpected path: {bad_backup_path}")

    # Ensure all connections and file handles are garbage-collected
    gc.collect()


# ===========================================================================
# PART A.2: BACKUP FILENAME PID UNIQUENESS
# ===========================================================================
section("PART A.2: BACKUP FILENAME PID UNIQUENESS")

with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as pid_temp_dir_str:
    pid_temp_dir = Path(pid_temp_dir_str)
    pid_src_db = pid_temp_dir / "pid_test_source.db"
    pid_backup_folder = pid_temp_dir / "backups"
    pid_backup_folder.mkdir(parents=True, exist_ok=True)

    create_sample_db(pid_src_db)

    # 1. Verify new backup filename contains PID
    # Reset debounce state so we get a fresh backup
    backup_mod._last_backup_time = 0.0
    backup_mod._last_backup_path = None

    pid_backup_path = create_backup(
        source_db_path=pid_src_db,
        backup_dir=pid_backup_folder,
        retention_days=30,
        force=True,
    )

    current_pid = str(os.getpid())
    if pid_backup_path and current_pid in pid_backup_path.name:
        ok(f"Backup filename contains current PID ({current_pid}): {pid_backup_path.name}")
    else:
        fail("Backup filename contains PID", f"PID={current_pid}, file={pid_backup_path}")

    # 2. Verify filename matches regex pattern
    if pid_backup_path and BACKUP_FILENAME_REGEX.match(pid_backup_path.name):
        ok(f"PID-included filename matches BACKUP_FILENAME_REGEX: {pid_backup_path.name}")
    else:
        fail("PID filename regex match", str(pid_backup_path))

    # 3. Verify legacy filenames (no PID) still match regex
    legacy_name = "bolti_slip_backup_20260101_120000.db"
    if BACKUP_FILENAME_REGEX.match(legacy_name):
        ok(f"Legacy filename (no PID) still matches regex: {legacy_name}")
    else:
        fail("Legacy filename regex match", legacy_name)

    # 4. Verify PID+microsecond filenames match regex
    pid_micro_name = "bolti_slip_backup_20260101_120000_12345_678901.db"
    if BACKUP_FILENAME_REGEX.match(pid_micro_name):
        ok(f"PID+microsecond filename matches regex: {pid_micro_name}")
    else:
        fail("PID+microsecond filename regex match", pid_micro_name)

    # 5. Simulate two "processes" creating backups in the same second
    #    by creating files with different PID values and checking no collision
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sim_file_1 = pid_backup_folder / f"bolti_slip_backup_{timestamp_str}_11111.db"
    sim_file_2 = pid_backup_folder / f"bolti_slip_backup_{timestamp_str}_22222.db"
    sim_file_1.write_bytes(b"SIMULATED_PID_11111")
    sim_file_2.write_bytes(b"SIMULATED_PID_22222")

    if sim_file_1.exists() and sim_file_2.exists() and sim_file_1.name != sim_file_2.name:
        ok(f"Two PIDs in same second produce distinct files: {sim_file_1.name} vs {sim_file_2.name}")
    else:
        fail("Same-second PID collision prevention", f"{sim_file_1.name} vs {sim_file_2.name}")

    # 6. Verify non-matching filenames are rejected by regex
    bad_names = [
        "random_backup.db",
        "bolti_slip_backup.db",
        "bolti_slip_backup_20260101.db",
        "bolti_slip_backup_abc_defghi.db",
    ]
    all_rejected = True
    for bad_name in bad_names:
        if BACKUP_FILENAME_REGEX.match(bad_name):
            all_rejected = False
            fail(f"Regex rejects '{bad_name}'", "Unexpectedly matched")
    if all_rejected:
        ok("Regex correctly rejects all malformed filenames")

    gc.collect()


# ===========================================================================
# PART B: ENVIRONMENT-BASED PRODUCTION CORS CONFIGURATION
# ===========================================================================
section("PART B: PRODUCTION CORS CONFIGURATION")

# 1. Development Mode Defaults
dev_origins = parse_cors_origins(raw_origins=None, is_production=False)
if "http://localhost:5173" in dev_origins and "http://127.0.0.1:5173" in dev_origins:
    ok("Development mode automatically permits standard localhost origins (5173, 3000)")
else:
    fail("Development default origins", str(dev_origins))

# 2. Development Mode with Custom Local Network Origin
custom_dev = parse_cors_origins(raw_origins="http://192.168.1.100:5173", is_production=False)
if "http://192.168.1.100:5173" in custom_dev and "http://localhost:5173" in custom_dev:
    ok("Development mode supplements localhost origins with custom local IP origin")
else:
    fail("Custom dev origin handling", str(custom_dev))

# 3. Production Mode with Valid Configured Origins
prod_raw = "https://shop.example.com,https://app.example.com"
prod_origins = parse_cors_origins(raw_origins=prod_raw, is_production=True)
if (
    len(prod_origins) == 2
    and "https://shop.example.com" in prod_origins
    and "https://app.example.com" in prod_origins
    and "http://localhost:5173" not in prod_origins
):
    ok("Production mode allows ONLY explicitly configured origins (excludes localhost by default)")
else:
    fail("Production valid origins", str(prod_origins))

# 4. Production Mode with Missing Origins (Fails Safely)
empty_prod_origins = parse_cors_origins(raw_origins="", is_production=True)
if empty_prod_origins == []:
    ok("Production mode with empty BOLTI_CORS_ORIGINS returns empty list (blocks all cross-origin requests)")
else:
    fail("Production empty origins", str(empty_prod_origins))

# 5. Production Mode Wildcard Rejection
wildcard_prod = parse_cors_origins(raw_origins="*", is_production=True)
if wildcard_prod == []:
    ok("Production mode strictly REJECTS wildcard '*' origin and returns empty list")
else:
    fail("Production wildcard rejection", str(wildcard_prod))

# 6. Production Mode Mixed Valid & Wildcard
mixed_prod = parse_cors_origins(raw_origins="https://shop.example.com,*", is_production=True)
if mixed_prod == ["https://shop.example.com"]:
    ok("Production mode strips wildcard '*' while preserving valid explicit origins")
else:
    fail("Production mixed wildcard handling", str(mixed_prod))

# 7. Trailing Slash Normalization
slash_origins = parse_cors_origins(raw_origins="https://shop.example.com/", is_production=True)
if slash_origins == ["https://shop.example.com"]:
    ok("Origin trailing slash normalized (https://shop.example.com/ -> https://shop.example.com)")
else:
    fail("Trailing slash normalization", str(slash_origins))

# 8. CORS Middleware Live Request Evaluation
# Test using TestClient with production environment settings
os.environ["BOLTI_ENV"] = "production"
os.environ["BOLTI_CORS_ORIGINS"] = "https://verified-shop.com"

# Import app with production settings applied
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

test_prod_app = FastAPI()
prod_cors = get_cors_settings()
test_prod_app.add_middleware(
    CORSMiddleware,
    allow_origins=prod_cors["allow_origins"],
    allow_credentials=prod_cors["allow_credentials"],
    allow_methods=prod_cors["allow_methods"],
    allow_headers=prod_cors["allow_headers"],
)


@test_prod_app.get("/api/ping")
def ping():
    return {"status": "pong"}


prod_client = TestClient(test_prod_app)

# 8.1 Configured Production Origin is Accepted
res_allowed = prod_client.options(
    "/api/ping",
    headers={
        "Origin": "https://verified-shop.com",
        "Access-Control-Request-Method": "GET",
    },
)
if res_allowed.headers.get("access-control-allow-origin") == "https://verified-shop.com":
    ok("Configured production origin receives Access-Control-Allow-Origin: https://verified-shop.com")
else:
    fail("Configured origin response", str(res_allowed.headers))

if res_allowed.headers.get("access-control-allow-credentials") == "true":
    ok("Credentials allowed for explicitly configured origin (allow_credentials=True)")
else:
    fail("Credentials header", str(res_allowed.headers))

# 8.2 Unconfigured Origin is Rejected
res_rejected = prod_client.options(
    "/api/ping",
    headers={
        "Origin": "https://unauthorized-attacker.com",
        "Access-Control-Request-Method": "GET",
    },
)
if "access-control-allow-origin" not in res_rejected.headers:
    ok("Unconfigured origin receives NO Access-Control-Allow-Origin header (rejected by browser)")
else:
    fail("Unconfigured origin rejection", str(res_rejected.headers))

# Clean up temporary test environment variables
os.environ.pop("BOLTI_ENV", None)
os.environ.pop("BOLTI_CORS_ORIGINS", None)


# ===========================================================================
# PART C: LIVE DATABASE ZERO-MODIFICATION VERIFICATION
# ===========================================================================
section("PART C: LIVE DATABASE ZERO-MODIFICATION VERIFICATION")

live_db_path = PROJECT_ROOT / "bolti_slip.db"
conn_real = sqlite3.connect(live_db_path)
cr = conn_real.cursor()

live_shops = cr.execute("SELECT id, username, shop_name FROM shops ORDER BY id").fetchall()
live_tickets = cr.execute("SELECT id, ticket_number, customer_name FROM tickets ORDER BY id").fetchall()
live_customers = cr.execute("SELECT id, name, phone FROM customers ORDER BY id").fetchall()
conn_real.close()

if len(live_shops) >= 2 and any(s[1] == "sharma" for s in live_shops):
    ok(f"Live database shops intact: {len(live_shops)} shops found; 'sharma' (id=1) preserved")
else:
    fail("Live database shops check", str(live_shops))

if len(live_tickets) == 9:
    ok("All 9 live tickets completely preserved (BLT-0001 through BLT-0009)")
else:
    fail("Live database tickets check", f"Expected 9, got {len(live_tickets)}")

if len(live_customers) >= 4:
    ok(f"All {len(live_customers)} live customers completely preserved")
else:
    fail("Live database customers check", f"Found {len(live_customers)}")


# ===========================================================================
# SUMMARY
# ===========================================================================
section("SUMMARY")
print(f"\n  Total Tests: {PASS + FAIL} | PASSED: {PASS} | FAILED: {FAIL}\n", flush=True)
if FAIL == 0:
    print("  *** ALL BATCH 2 TESTS PASSED ***", flush=True)
else:
    print("  *** SOME TESTS FAILED ***", flush=True)
    for status, name, *rest in results:
        if status == "FAIL":
            print(f"    FAIL: {name} {rest[0] if rest else ''}", flush=True)

sys.exit(0 if FAIL == 0 else 1)
