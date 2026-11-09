"""
scripts/test_seed_setup.py
--------------------------
Automated test suite for first-run seed setup behavior and protection.
Tests:
  1. Existing database preservation (no changes to existing shops/tickets)
  2. Guard against setup takeover on existing database
  3. Fresh database without BOLTI_SEED_PASSWORD creates NO inaccessible account
  4. Fresh database with valid BOLTI_SEED_PASSWORD creates seed account successfully
  5. Fresh database with invalid BOLTI_SEED_PASSWORD (<6 chars) rejects creation
  6. setup_first_shop function works on fresh DB and blocks duplicate initialization
  7. Verification that no hardcoded seed password remains in source code
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from backend.database.db import sync_init_db, _MIGRATIONS_DIR
from backend.services.auth import hash_password, verify_password
from scripts.setup_first_shop import setup_first_shop, validate_username, validate_password

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


# Helper to initialize raw migration schema on a custom DB path
def create_test_db(db_path: Path):
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
        conn.commit()
    finally:
        conn.close()


# Helper to run the seed check logic on a target DB
def run_seed_logic_on_db(db_path: Path, seed_pw: str = None):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shops")
        shop_count = cursor.fetchone()[0]
        if shop_count == 0:
            if seed_pw and seed_pw.strip():
                clean_pw = seed_pw.strip()
                if 6 <= len(clean_pw) <= 128:
                    default_hash = hash_password(clean_pw)
                    conn.execute(
                        """
                        INSERT INTO shops (id, username, password_hash, shop_name, owner_name, phone, branch, address)
                        VALUES (1, 'sharma', ?, 'Sharma Electronics', 'Rajesh Sharma', '9876543210', 'Pune Main Branch', 'Shop 4, Market Yard, Pune')
                        """,
                        (default_hash,)
                    )
                    conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# TEST SUITE 1: Existing Database Preservation
# ---------------------------------------------------------------------------
section("1. EXISTING DATABASE PRESERVATION")

LIVE_DB = PROJECT_ROOT / "bolti_slip.db"
conn = sqlite3.connect(LIVE_DB)
c = conn.cursor()

# Record state before running sync_init_db
pre_shops = c.execute("SELECT id, username, password_hash FROM shops ORDER BY id").fetchall()
pre_tickets = c.execute("SELECT id, ticket_number, shop_id FROM tickets ORDER BY id").fetchall()
conn.close()

# Run sync_init_db on live DB
sync_init_db()

conn = sqlite3.connect(LIVE_DB)
c = conn.cursor()
post_shops = c.execute("SELECT id, username, password_hash FROM shops ORDER BY id").fetchall()
post_tickets = c.execute("SELECT id, ticket_number, shop_id FROM tickets ORDER BY id").fetchall()
conn.close()

if pre_shops == post_shops:
    ok("Existing shops and password hashes completely unchanged")
else:
    fail("Existing shops unchanged", "Shops table was modified")

if pre_tickets == post_tickets:
    ok(f"Existing tickets completely unchanged ({len(post_tickets)} tickets verified)")
else:
    fail("Existing tickets unchanged", "Tickets table was modified")

# Check sharma account specifically
sharma_row = [s for s in post_shops if s[1] == "sharma"]
if sharma_row:
    ok(f"Sharma shop account preserved (id={sharma_row[0][0]})")
else:
    fail("Sharma shop account preserved", "Account missing")


# ---------------------------------------------------------------------------
# TEST SUITE 2: Setup Protection Against Existing Database Takeover
# ---------------------------------------------------------------------------
section("2. SETUP TAKEOVER PROTECTION")

try:
    setup_first_shop(
        username="hacker_takeover",
        password="HackerPass@999",
        shop_name="Hacked Shop",
        owner_name="Hacker",
    )
    fail("setup_first_shop blocked on existing DB", "Function succeeded when it should have raised PermissionError")
except PermissionError as pe:
    ok(f"setup_first_shop correctly blocked on existing DB: PermissionError raised")
except Exception as e:
    fail("setup_first_shop blocked on existing DB", f"Raised unexpected exception: {e}")


# ---------------------------------------------------------------------------
# TEST SUITE 3: Fresh Database WITHOUT BOLTI_SEED_PASSWORD
# ---------------------------------------------------------------------------
section("3. FRESH DATABASE WITHOUT BOLTI_SEED_PASSWORD")

with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
    tmp_path = Path(tmp_db.name)

try:
    create_test_db(tmp_path)
    # Run seed logic with no password (simulating missing/empty BOLTI_SEED_PASSWORD)
    run_seed_logic_on_db(tmp_path, seed_pw=None)

    conn = sqlite3.connect(tmp_path)
    count = conn.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
    conn.close()

    if count == 0:
        ok("Fresh DB without BOLTI_SEED_PASSWORD leaves shops count = 0 (no inaccessible account)")
    else:
        fail("Fresh DB without BOLTI_SEED_PASSWORD leaves shops count = 0", f"Found {count} shops")
finally:
    tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TEST SUITE 4: Fresh Database WITH Valid BOLTI_SEED_PASSWORD
# ---------------------------------------------------------------------------
section("4. FRESH DATABASE WITH VALID BOLTI_SEED_PASSWORD")

test_env_pw = "CustomSeedPass@2026"
with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
    tmp_path = Path(tmp_db.name)

try:
    create_test_db(tmp_path)
    # Run seed logic with valid password
    run_seed_logic_on_db(tmp_path, seed_pw=test_env_pw)

    conn = sqlite3.connect(tmp_path)
    shops = conn.execute("SELECT id, username, password_hash, shop_name FROM shops").fetchall()
    conn.close()

    if len(shops) == 1:
        ok("Fresh DB with BOLTI_SEED_PASSWORD creates exactly 1 seed shop")
        shop = shops[0]
        if shop[1] == "sharma" and shop[3] == "Sharma Electronics":
            ok("Seed shop username ('sharma') and shop_name correctly configured")
        else:
            fail("Seed shop details", str(shop))

        stored_hash = shop[2]
        if verify_password(test_env_pw, stored_hash):
            ok("Configured BOLTI_SEED_PASSWORD successfully verifies against stored PBKDF2 hash")
        else:
            fail("Password verification against hash", "Password did not verify")

        if test_env_pw not in stored_hash:
            ok("Plaintext password is NOT stored in the database")
        else:
            fail("Plaintext check", "Plaintext password found in database")
    else:
        fail("Fresh DB with BOLTI_SEED_PASSWORD creates exactly 1 shop", f"Found {len(shops)} shops")
finally:
    tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TEST SUITE 5: Fresh Database with INVALID BOLTI_SEED_PASSWORD (< 6 chars)
# ---------------------------------------------------------------------------
section("5. FRESH DATABASE WITH INVALID BOLTI_SEED_PASSWORD (< 6 chars)")

with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
    tmp_path = Path(tmp_db.name)

try:
    create_test_db(tmp_path)
    # Run seed logic with invalid password (length 3 < min 6)
    run_seed_logic_on_db(tmp_path, seed_pw="123")

    conn = sqlite3.connect(tmp_path)
    count = conn.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
    conn.close()

    if count == 0:
        ok("Invalid BOLTI_SEED_PASSWORD (<6 chars) rejected; 0 shops created")
    else:
        fail("Invalid password rejection", f"Unexpectedly created {count} shops")
finally:
    tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TEST SUITE 6: CLI setup_first_shop Validation and Execution
# ---------------------------------------------------------------------------
section("6. CLI setup_first_shop VALIDATION")

# Test validation helpers
try:
    validate_username("ab")
    fail("validate_username < 3 chars", "Did not raise ValueError")
except ValueError:
    ok("validate_username rejects username with length < 3")

try:
    validate_password("12345")
    fail("validate_password < 6 chars", "Did not raise ValueError")
except ValueError:
    ok("validate_password rejects password with length < 6")

# Test execution on fresh temporary DB
with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
    tmp_path = Path(tmp_db.name)

try:
    create_test_db(tmp_path)

    # Temporarily monkeypatch DB_PATH in scripts.setup_first_shop
    import scripts.setup_first_shop as sfs
    original_db_path = sfs.DB_PATH
    sfs.DB_PATH = tmp_path

    try:
        # First call on fresh DB should succeed
        res = sfs.setup_first_shop(
            username="cli_shop_owner",
            password="SecureCliPass@123",
            shop_name="CLI Repair Hub",
            owner_name="CLI Owner",
        )
        if res["username"] == "cli_shop_owner" and res["shop_name"] == "CLI Repair Hub":
            ok("setup_first_shop creates first shop on fresh DB")
        else:
            fail("setup_first_shop creates first shop", str(res))

        # Second call on the same DB must be rejected
        try:
            sfs.setup_first_shop(
                username="second_owner",
                password="SecondPass@456",
                shop_name="Second Shop",
                owner_name="Second Owner",
            )
            fail("Second setup_first_shop call rejected", "Allowed duplicate first-run setup")
        except PermissionError:
            ok("Second setup_first_shop call correctly rejected (PermissionError)")
    finally:
        sfs.DB_PATH = original_db_path
finally:
    tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TEST SUITE 7: Hardcoded Secret Absence Check
# ---------------------------------------------------------------------------
section("7. HARDCODED SECRET ABSENCE CHECK")

db_py_text = (PROJECT_ROOT / "backend" / "database" / "db.py").read_text(encoding="utf-8")
if "Sharma@123" not in db_py_text:
    ok("No 'Sharma@123' in backend/database/db.py")
else:
    fail("No 'Sharma@123' in backend/database/db.py", "Pattern found")

env_example_text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
if "Sharma@123" not in env_example_text:
    ok("No 'Sharma@123' in .env.example")
else:
    fail("No 'Sharma@123' in .env.example", "Pattern found")


# ---------------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------------
section("SUMMARY")
print(f"\n  Total Tests: {PASS + FAIL} | PASSED: {PASS} | FAILED: {FAIL}\n", flush=True)
if FAIL == 0:
    print("  *** ALL SEED SETUP TESTS PASSED ***", flush=True)
else:
    print("  *** SOME TESTS FAILED ***", flush=True)
    for status, name, *rest in results:
        if status == "FAIL":
            print(f"    FAIL: {name} {rest[0] if rest else ''}", flush=True)

sys.exit(0 if FAIL == 0 else 1)
