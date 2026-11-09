"""
scripts/setup_first_shop.py
----------------------------
Safe first-run CLI setup utility for Bolti Slip.

Use this script to create the initial shopkeeper account when installing
Bolti Slip for the first time without using the web interface or
BOLTI_SEED_PASSWORD environment variable.

Security Rules:
- Only runs when the `shops` table is completely empty (COUNT(*) == 0).
- If shops already exist, immediately exits to prevent account takeover or password resets.
- Enforces normal registration validation rules (username 3-50 chars, password 6-128 chars).
- Uses PBKDF2-HMAC-SHA256 (600,000 iterations, 32-byte salt).
- Never prints passwords to logs, terminals, or reports.
"""

import argparse
import getpass
import os
import re
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.auth import hash_password

DB_PATH = PROJECT_ROOT / "bolti_slip.db"


def validate_username(username: str) -> str:
    username = username.strip().lower()
    if not (3 <= len(username) <= 50):
        raise ValueError("Username must be between 3 and 50 characters.")
    if not re.match(r"^[a-zA-Z0-9_\-]+$", username):
        raise ValueError("Username may only contain letters, numbers, hyphens, and underscores.")
    return username


def validate_password(password: str) -> str:
    if not (6 <= len(password) <= 128):
        raise ValueError("Password must be between 6 and 128 characters.")
    return password


def setup_first_shop(username: str, password: str, shop_name: str, owner_name: str,
                     phone: str = "", branch: str = "Main Branch", address: str = "") -> dict:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run the backend server once to initialize schema.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Security Guard: Only allow execution if ZERO shops exist
        cursor.execute("SELECT COUNT(*) FROM shops")
        shop_count = cursor.fetchone()[0]
        if shop_count > 0:
            raise PermissionError(
                "Setup aborted: One or more shop accounts already exist in the database. "
                "This setup script only runs on a fresh database to prevent account takeover or password overwrites. "
                "To create additional shops, please use the web registration page (/register) or log in."
            )

        clean_user = validate_username(username)
        clean_pass = validate_password(password)
        clean_shop = shop_name.strip()
        clean_owner = owner_name.strip()

        if not clean_shop:
            raise ValueError("Shop name cannot be empty.")
        if not clean_owner:
            raise ValueError("Owner name cannot be empty.")

        pwd_hash = hash_password(clean_pass)

        try:
            cursor.execute(
                """
                INSERT INTO shops (id, username, password_hash, shop_name, owner_name, phone, branch, address)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_user,
                    pwd_hash,
                    clean_shop,
                    clean_owner,
                    phone.strip() if phone else None,
                    branch.strip() if branch else "Main Branch",
                    address.strip() if address else None,
                ),
            )
            shop_id = cursor.lastrowid

            # Backfill any pre-existing tickets without shop_id to this first shop
            cursor.execute("UPDATE tickets SET shop_id = ? WHERE shop_id IS NULL", (shop_id,))
            conn.commit()
        except sqlite3.IntegrityError as ie:
            # Check if another process created a shop concurrently
            cursor.execute("SELECT COUNT(*) FROM shops")
            if cursor.fetchone()[0] > 0:
                raise PermissionError(
                    "Setup aborted: A shop account was created concurrently by another process. "
                    "This setup script only runs on a fresh database to prevent account takeover or password overwrites."
                ) from ie
            raise

        return {
            "id": shop_id,
            "username": clean_user,
            "shop_name": clean_shop,
            "owner_name": clean_owner,
        }
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Bolti Slip — Safe First-Run Shopkeeper Setup")
    parser.add_argument("--username", help="Shopkeeper login username (3-50 chars)")
    parser.add_argument("--password", help="Shopkeeper login password (6-128 chars)")
    parser.add_argument("--shop-name", help="Shop name (e.g. Sharma Electronics)")
    parser.add_argument("--owner-name", help="Owner name (e.g. Rajesh Sharma)")
    parser.add_argument("--phone", default="", help="Contact phone number (optional)")
    parser.add_argument("--branch", default="Main Branch", help="Branch name (optional)")
    parser.add_argument("--address", default="", help="Shop address (optional)")

    args = parser.parse_args()

    print("\n============================================================")
    print("  Bolti Slip — First-Run Shopkeeper Account Setup")
    print("============================================================\n")

    # Interactive prompts if arguments not supplied
    try:
        username = args.username or input("Enter shopkeeper username (min 3 chars): ").strip()
        validate_username(username)

        if args.password:
            password = args.password
        else:
            password = getpass.getpass("Enter shopkeeper password (min 6 chars): ")
            confirm = getpass.getpass("Confirm shopkeeper password: ")
            if password != confirm:
                print("\n[ERROR] Passwords do not match.")
                sys.exit(1)
        validate_password(password)

        shop_name = args.shop_name or input("Enter shop name: ").strip()
        owner_name = args.owner_name or input("Enter owner name: ").strip()
        phone = args.phone or input("Enter phone number (optional): ").strip()
        branch = args.branch or input("Enter branch [Main Branch]: ").strip() or "Main Branch"
        address = args.address or input("Enter shop address (optional): ").strip()

        result = setup_first_shop(
            username=username,
            password=password,
            shop_name=shop_name,
            owner_name=owner_name,
            phone=phone,
            branch=branch,
            address=address,
        )

        print("\n[SUCCESS] First shop account created successfully!")
        print(f"  Shop ID    : {result['id']}")
        print(f"  Username   : {result['username']}")
        print(f"  Shop Name  : {result['shop_name']}")
        print(f"  Owner Name : {result['owner_name']}")
        print("\nYou can now start the Bolti Slip server and log in.\n")

    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
