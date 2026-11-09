"""
scripts/cleanup_test_accounts.py
---------------------------------
Controlled, transactional cleanup of the 11 ephemeral test accounts (IDs 3-13)
identified in DATABASE_ACCOUNT_INSPECTION.md.

Safety features:
- Requires pre-verification of all 11 account IDs, usernames, and zero tickets/customers.
- Verifies preservation of Shop 1 (sharma) and Shop 2 (testshop).
- Executes within an atomic SQLite transaction with immediate rollback on any discrepancy.
- Validates PRAGMA integrity_check and PRAGMA foreign_key_check post-cleanup.
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "bolti_slip.db"

EXPECTED_TEST_ACCOUNTS = {
    3: "tuser_97c5ee13",
    4: "reg_user_78e199",
    5: "tuser_c8111c0c",
    6: "tuser_6063d81c",
    7: "reg_user_0fd7b4",
    8: "tuser_6b9ccbc3",
    9: "reg_user_3c8bdf",
    10: "tuser_b54b0dcc",
    11: "reg_user_7d7836",
    12: "tuser_b820e0ad",
    13: "reg_user_541a0b",
}


def run_cleanup():
    print(f"Connecting to live database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    try:
        # =====================================================================
        # STEP 2: PRE-DELETION VERIFICATION
        # =====================================================================
        print("\n--- STEP 2: PRE-DELETION VERIFICATION ---")

        # 1. Verify shops count and identities
        all_shops = c.execute("SELECT id, username FROM shops ORDER BY id").fetchall()
        print(f"Total shops found: {len(all_shops)}")
        if len(all_shops) != 13:
            raise ValueError(f"Aborting: Expected 13 shops, found {len(all_shops)}")

        if all_shops[0] != (1, "sharma"):
            raise ValueError(f"Aborting: Shop 1 is not 'sharma': {all_shops[0]}")
        if all_shops[1] != (2, "testshop"):
            raise ValueError(f"Aborting: Shop 2 is not 'testshop': {all_shops[1]}")

        # Check each test shop ID 3-13 against expected username
        found_test_accounts = dict(all_shops[2:])
        if found_test_accounts != EXPECTED_TEST_ACCOUNTS:
            raise ValueError(
                f"Aborting: Shop IDs 3-13 do not match expected accounts!\n"
                f"Found: {found_test_accounts}\nExpected: {EXPECTED_TEST_ACCOUNTS}"
            )
        print("Pre-check: Shop IDs 3-13 exactly match the 11 confirmed test accounts.")

        # 2. Verify tickets
        total_tickets = c.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        test_shop_tickets = c.execute(
            "SELECT COUNT(*) FROM tickets WHERE shop_id NOT IN (1, 2)"
        ).fetchone()[0]
        shop1_tickets = c.execute("SELECT COUNT(*) FROM tickets WHERE shop_id = 1").fetchone()[0]
        shop2_tickets = c.execute("SELECT COUNT(*) FROM tickets WHERE shop_id = 2").fetchone()[0]

        print(f"Tickets verification: Total={total_tickets}, Shop1={shop1_tickets}, Shop2={shop2_tickets}, TestShops={test_shop_tickets}")
        if total_tickets != 9 or shop1_tickets != 8 or shop2_tickets != 1 or test_shop_tickets != 0:
            raise ValueError("Aborting: Ticket counts do not match expected production state!")

        # 3. Verify customers
        total_customers = c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        test_shop_customers = c.execute(
            "SELECT COUNT(*) FROM customers WHERE shop_id NOT IN (1, 2)"
        ).fetchone()[0]
        shop1_customers = c.execute("SELECT COUNT(*) FROM customers WHERE shop_id = 1").fetchone()[0]
        shop2_customers = c.execute("SELECT COUNT(*) FROM customers WHERE shop_id = 2").fetchone()[0]

        print(f"Customers verification: Total={total_customers}, Shop1={shop1_customers}, Shop2={shop2_customers}, TestShops={test_shop_customers}")
        if total_customers != 4 or shop1_customers != 3 or shop2_customers != 1 or test_shop_customers != 0:
            raise ValueError("Aborting: Customer counts do not match expected production state!")

        # 4. Verify sessions
        total_sessions = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        legit_sessions = c.execute("SELECT COUNT(*) FROM sessions WHERE shop_id IN (1, 2)").fetchone()[0]
        test_sessions = c.execute("SELECT COUNT(*) FROM sessions WHERE shop_id NOT IN (1, 2)").fetchone()[0]
        print(f"Sessions verification: Total={total_sessions}, LegitShops(1,2)={legit_sessions}, TestShops(3-13)={test_sessions}")
        if total_sessions != 20 or legit_sessions != 5 or test_sessions != 15:
            raise ValueError("Aborting: Session counts do not match expected count (expected 15 test sessions)!")

        print("Pre-deletion verification PASSED on all checks.\n")

        # =====================================================================
        # STEP 3: CONTROLLED DELETION (SINGLE TRANSACTION)
        # =====================================================================
        print("--- STEP 3: EXECUTING TRANSACTIONAL DELETION ---")
        conn.execute("BEGIN IMMEDIATE TRANSACTION;")

        test_ids = tuple(sorted(EXPECTED_TEST_ACCOUNTS.keys()))

        # A. Delete dependent sessions for test shops
        cur_sess = conn.execute(
            f"DELETE FROM sessions WHERE shop_id IN ({','.join('?' for _ in test_ids)})",
            test_ids,
        )
        print(f"Deleted {cur_sess.rowcount} test session records (expected 15).")
        if cur_sess.rowcount != 15:
            raise ValueError(f"Aborting: Unexpected session deletion count: {cur_sess.rowcount}")

        # B. Delete test shops explicitly matching IDs and username patterns
        cur_shops = conn.execute(
            f"""
            DELETE FROM shops 
            WHERE id IN ({','.join('?' for _ in test_ids)}) 
              AND (username LIKE 'tuser_%' OR username LIKE 'reg_user_%')
            """,
            test_ids,
        )
        print(f"Deleted {cur_shops.rowcount} test shop records (expected 11).")
        if cur_shops.rowcount != 11:
            raise ValueError(f"Aborting: Unexpected shop deletion count: {cur_shops.rowcount}")

        # C. In-transaction assertion checks
        remaining_shops = c.execute("SELECT id, username, shop_name FROM shops ORDER BY id").fetchall()
        if len(remaining_shops) != 2 or remaining_shops[0][0] != 1 or remaining_shops[1][0] != 2:
            raise ValueError(f"Aborting: Post-deletion shop check failed: {remaining_shops}")

        remaining_tickets = c.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if remaining_tickets != 9:
            raise ValueError(f"Aborting: Tickets modified! Expected 9, got {remaining_tickets}")

        remaining_customers = c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if remaining_customers != 4:
            raise ValueError(f"Aborting: Customers modified! Expected 4, got {remaining_customers}")

        remaining_sessions = c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        if remaining_sessions != 5:
            raise ValueError(f"Aborting: Sessions count mismatch! Expected 5, got {remaining_sessions}")

        # Commit transaction
        conn.commit()
        print("TRANSACTION COMMITTED SUCCESSFULLY.\n")

        # =====================================================================
        # STEP 4: POST-DELETION VERIFICATION & INTEGRITY CHECK
        # =====================================================================
        print("--- STEP 4: POST-DELETION VERIFICATION ---")

        # PRAGMA integrity_check
        integrity = c.execute("PRAGMA integrity_check;").fetchall()
        print(f"PRAGMA integrity_check: {integrity}")
        if integrity != [("ok",)]:
            raise ValueError(f"Integrity check failed: {integrity}")

        # PRAGMA foreign_key_check
        fk_check = c.execute("PRAGMA foreign_key_check;").fetchall()
        print(f"PRAGMA foreign_key_check: {fk_check}")
        if fk_check != []:
            raise ValueError(f"Foreign key violations found: {fk_check}")

        # Final counts
        final_shops = c.execute("SELECT id, username, shop_name, owner_name FROM shops ORDER BY id").fetchall()
        final_tickets = c.execute("SELECT count(*) FROM tickets").fetchone()[0]
        final_customers = c.execute("SELECT count(*) FROM customers").fetchone()[0]
        final_sessions = c.execute("SELECT count(*) FROM sessions").fetchone()[0]

        print("\nFINAL STATE:")
        print(f"  Shops: {len(final_shops)}")
        for s in final_shops:
            t_cnt = c.execute("SELECT count(*) FROM tickets WHERE shop_id = ?", (s[0],)).fetchone()[0]
            c_cnt = c.execute("SELECT count(*) FROM customers WHERE shop_id = ?", (s[0],)).fetchone()[0]
            sess_cnt = c.execute("SELECT count(*) FROM sessions WHERE shop_id = ?", (s[0],)).fetchone()[0]
            print(f"    ID {s[0]}: {s[1]} ({s[2]}) | Owner: {s[3]} | Tickets: {t_cnt} | Customers: {c_cnt} | Sessions: {sess_cnt}")

        print(f"  Total Tickets: {final_tickets}")
        print(f"  Total Customers: {final_customers}")
        print(f"  Total Sessions: {final_sessions}")
        print("\nALL POST-DELETION VERIFICATIONS PASSED (100% OK).")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] An error occurred: {e}", file=sys.stderr)
        print("[INFO] Transaction rolled back safely. Database unchanged.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    conn.close()


if __name__ == "__main__":
    run_cleanup()
