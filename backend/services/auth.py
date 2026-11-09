"""
backend/services/auth.py
------------------------
Authentication and password security service for Bolti Slip.
- Zero-external-dependency password hashing using PBKDF2-HMAC-SHA256 (600,000 rounds).
- Token-based session management stored in SQLite with 30-day expiry.
- FastAPI dependency `get_current_shop` for multi-tenant route protection.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import aiosqlite
from fastapi import Depends, Header, HTTPException, status

from backend.database.db import get_db

ITERATIONS = 600_000
ALGORITHM = "sha256"
SESSION_DURATION_DAYS = 30


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a 32-byte random salt."""
    salt = secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac(ALGORITHM, password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2:{ALGORITHM}:{ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored PBKDF2 hash string."""
    try:
        parts = hashed.split("$")
        if len(parts) != 3:
            return False
        meta, salt_hex, key_hex = parts
        _, algo, iters = meta.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        computed_key = hashlib.pbkdf2_hmac(algo, password.encode("utf-8"), salt, int(iters))
        return secrets.compare_digest(key, computed_key)
    except Exception:
        return False


async def create_session(db: aiosqlite.Connection, shop_id: int, days: int = SESSION_DURATION_DAYS) -> str:
    """Generate a cryptographic session token and persist it in the sessions table."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=days)).isoformat()

    await db.execute(
        """
        INSERT INTO sessions (token, shop_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (token, shop_id, now.isoformat(), expires_at),
    )
    await db.commit()
    return token


async def delete_session(db: aiosqlite.Connection, token: str) -> bool:
    """Invalidate a session token on logout."""
    cursor = await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    await db.commit()
    return cursor.rowcount > 0


async def revoke_other_sessions(db: aiosqlite.Connection, shop_id: int, keep_token: Optional[str] = None) -> int:
    """Revoke all sessions for a shop, optionally preserving keep_token."""
    if keep_token:
        cursor = await db.execute(
            "DELETE FROM sessions WHERE shop_id = ? AND token != ?",
            (shop_id, keep_token),
        )
    else:
        cursor = await db.execute(
            "DELETE FROM sessions WHERE shop_id = ?",
            (shop_id,),
        )
    await db.commit()
    return cursor.rowcount


async def get_shop_by_token(db: aiosqlite.Connection, token: str) -> Optional[dict]:
    """Retrieve active shop details associated with an unexpired session token."""
    now_iso = datetime.now(timezone.utc).isoformat()
    query = """
        SELECT s.id, s.username, s.shop_name, s.owner_name, s.phone, s.branch, s.address, s.created_at
        FROM sessions sess
        JOIN shops s ON sess.shop_id = s.id
        WHERE sess.token = ? AND sess.expires_at > ?
    """
    cursor = await db.execute(query, (token, now_iso))
    row = await cursor.fetchone()
    if row:
        return dict(row)
    return None


async def get_current_shop(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """
    FastAPI dependency: extracts and validates Bearer token.
    Raises HTTP 401 if missing, invalid, or expired.
    Returns the authenticated shop record dict.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    shop = await get_shop_by_token(db, token)
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return shop
