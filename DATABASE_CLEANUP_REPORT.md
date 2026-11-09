# Controlled Database Cleanup Report — Removal of 11 Test Accounts

**Date:** 2026-11-09  
**Database Path:** `C:\Programs\Project\Bolti-Slip\bolti_slip.db`  
**Status:** Completed Successfully (Transaction Committed & Verified)

---

## 1. Executive Summary

A controlled, transactional cleanup of the 11 ephemeral test accounts (shop IDs 3–13) was executed on the live SQLite database `bolti_slip.db`.

Prior to deletion:
- A full SQLite online backup was generated and verified with `PRAGMA integrity_check`.
- Pre-deletion checks verified that shop IDs 3–13 matched the confirmed test account usernames and had 0 associated tickets and 0 associated customers.
- Primary shop accounts 1 (`sharma`) and 2 (`testshop`) were confirmed intact along with all 9 tickets and 4 customers.

During deletion:
- The 15 dependent test sessions belonging to shops 3–13 were safely deleted.
- The 11 test shop records (IDs 3–13) were deleted in a single immediate transaction.
- In-transaction safety assertions confirmed zero changes to legitimate accounts before committing.

Post-deletion:
- `PRAGMA integrity_check` returned `ok`.
- `PRAGMA foreign_key_check` returned empty (0 violations).
- The final database contains exactly **2 shops**, **9 tickets**, and **4 customers**.

---

## 2. Step 1: Safety Backup

- **Backup Mechanism:** Python native `Connection.backup()` via `backend.database.backup.create_backup(force=True)`.
- **Verified Backup File Path:**
  `C:\Programs\Project\Bolti-Slip\backups\bolti_slip_backup_20261109_075339_8968.db`
- **Integrity Verification:**
  ```sql
  PRAGMA integrity_check;
  -- Result: ok
  ```
- **Validation Status:** PASSED (Verified before proceeding to deletion).

---

## 3. Step 2: Pre-Deletion Verification

Before any deletion was attempted, all entities and constraints were inspected:

| Entity / Metric | Expected Value | Observed Value | Match Status |
| :--- | :---: | :---: | :---: |
| Total Initial Shops | 13 | 13 | MATCH |
| Shop 1 Identity | `(1, 'sharma')` | `(1, 'sharma')` | MATCH |
| Shop 2 Identity | `(2, 'testshop')` | `(2, 'testshop')` | MATCH |
| Test Shop IDs | 3 through 13 | 3 through 13 | MATCH |
| Test Usernames | Matches `DATABASE_ACCOUNT_INSPECTION.md` | All 11 matched | MATCH |
| Total Tickets | 9 | 9 | MATCH |
| Tickets under Test Shops (3–13) | 0 | 0 | MATCH |
| Total Customers | 4 | 4 | MATCH |
| Customers under Test Shops (3–13) | 0 | 0 | MATCH |
| Total Sessions | 20 | 20 | MATCH |
| Sessions under Legit Shops (1, 2) | 5 (3 for Shop 1, 2 for Shop 2) | 5 | MATCH |
| Sessions under Test Shops (3–13) | 15 | 15 | MATCH |

---

## 4. Step 3: Controlled Deletion Details

Execution was performed atomically via `scripts/cleanup_test_accounts.py` wrapped in `BEGIN IMMEDIATE TRANSACTION;`:

```sql
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE TRANSACTION;

-- 1. Delete dependent sessions for test shops (Row count = 15)
DELETE FROM sessions WHERE shop_id IN (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13);

-- 2. Delete test shops strictly matching ID and test username pattern (Row count = 11)
DELETE FROM shops 
WHERE id IN (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13)
  AND (username LIKE 'tuser_%' OR username LIKE 'reg_user_%');

-- In-transaction safety checks passed -> COMMIT
COMMIT;
```

### Accounts Deleted

| Shop ID | Username | Shop Name | Sessions Removed |
| :---: | :--- | :--- | :---: |
| **3** | `tuser_97c5ee13` | Test Shop Revocation | 1 |
| **4** | `reg_user_78e199` | Non-blocked Shop | 1 |
| **5** | `tuser_c8111c0c` | Test Shop Revocation | 1 |
| **6** | `tuser_6063d81c` | Test Shop Revocation | 2 |
| **7** | `reg_user_0fd7b4` | Non-blocked Shop | 1 |
| **8** | `tuser_6b9ccbc3` | Test Shop Revocation | 2 |
| **9** | `reg_user_3c8bdf` | Non-blocked Shop | 1 |
| **10** | `tuser_b54b0dcc` | Test Shop Revocation | 2 |
| **11** | `reg_user_7d7836` | Non-blocked Shop | 1 |
| **12** | `tuser_b820e0ad` | Test Shop Revocation | 2 |
| **13** | `reg_user_541a0b` | Non-blocked Shop | 1 |
| **TOTAL** | **11 shops** | — | **15 sessions** |

---

## 5. Step 4: Post-Deletion Verification & Database State

| Table / Check | Pre-Cleanup Baseline | Post-Cleanup State | Status |
| :--- | :---: | :---: | :---: |
| `shops` | 13 | **2** | CLEANED (11 removed) |
| `tickets` | 9 | **9** | UNTOUCHED (0 deleted) |
| `customers` | 4 | **4** | UNTOUCHED (0 deleted) |
| `sessions` | 20 | **5** | CLEANED (15 removed) |
| `PRAGMA integrity_check` | ok | **ok** | PASS |
| `PRAGMA foreign_key_check` | ok | **ok (0 violations)** | PASS |

### Preserved Primary Shop Accounts

- **Shop ID 1 (`sharma`)**:
  - Username: `sharma`
  - Shop Name: Sharma Electronics
  - Owner: Rajesh Sharma
  - Phone: `9876543210`
  - Branch: Pune Main Branch
  - Address: Shop 4, Market Yard, Pune
  - Tickets: **8 tickets** (BLT-0001 through BLT-0008)
  - Customers: **3 customers** (Priya Sharma, Ramesh Kumar, Ziyan)
  - Active Sessions: **3 sessions**
- **Shop ID 2 (`testshop`)**:
  - Username: `testshop`
  - Shop Name: Test Electronics
  - Owner: Test Owner
  - Branch: Main Branch
  - Address: Test Address, Pune
  - Tickets: **1 ticket** (BLT-0009 — "Laptop")
  - Customers: **1 customer** (Ziyan)
  - Active Sessions: **2 sessions**

---

## 6. Automated Regression Verification

Following cleanup, the full test suite was re-executed against the project:

- `scripts/test_batch1_security.py` (Isolated DB): **33 / 33 PASSED** (Confirmed zero live DB writes)
- `scripts/test_batch2_security.py`: **31 / 31 PASSED** (Confirmed live DB intact with 2 shops)
- `scripts/test_seed_setup.py`: **16 / 16 PASSED**
- `scripts/test_batch1_2_fixes.py`: **18 / 18 PASSED**

---

## 7. Compliance Checklist

- [x] Pre-deletion safety backup verified with `PRAGMA integrity_check`.
- [x] Verification of each individual account ID and username before deletion.
- [x] Verification that 0 tickets and 0 customers were linked to test shops.
- [x] Single immediate atomic transaction with automatic rollback safeguard.
- [x] Foreign-key relationships and sessions verified before and after.
- [x] No broad deletion used (`WHERE 1=1` or unbounded ID range without conditions).
- [x] Database was not recreated or migrated.
- [x] No Git commit, push, or deployment was performed.
