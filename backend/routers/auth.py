"""
backend/routers/auth.py
-----------------------
Endpoints for shopkeeper registration, login, profile, and logout.

Routes:
POST /api/auth/register  — Register new shopkeeper account
POST /api/auth/login     — Login with username and password
GET  /api/auth/me        — Get currently authenticated shop profile
POST /api/auth/logout    — Invalidate session token
"""

from typing import Optional
import aiosqlite
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from backend.database.db import get_db
from backend.models.auth import AuthResponse, PasswordChangeRequest, ShopLogin, ShopRegister, ShopResponse
from backend.services.auth import (
    create_session,
    delete_session,
    get_current_shop,
    hash_password,
    revoke_other_sessions,
    verify_password,
)
from backend.services.limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: ShopRegister, db: aiosqlite.Connection = Depends(get_db)):
    """Register a new shopkeeper account and return an active session token."""
    # Check if username is already taken (case-insensitive)
    cursor = await db.execute("SELECT id FROM shops WHERE LOWER(username) = LOWER(?)", (body.username,))
    existing = await cursor.fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already registered. Please choose another username.",
        )

    pwd_hash = hash_password(body.password)
    cursor = await db.execute(
        """
        INSERT INTO shops (username, password_hash, shop_name, owner_name, phone, branch, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            body.username.strip().lower(),
            pwd_hash,
            body.shop_name.strip(),
            body.owner_name.strip(),
            body.phone.strip() if body.phone else None,
            body.branch.strip() if body.branch else "Main Branch",
            body.address.strip() if body.address else None,
        ),
    )
    await db.commit()
    shop_id = cursor.lastrowid

    # Retrieve created shop record
    cursor = await db.execute(
        "SELECT id, username, shop_name, owner_name, phone, branch, address, created_at FROM shops WHERE id = ?",
        (shop_id,),
    )
    shop_row = await cursor.fetchone()
    shop_dict = dict(shop_row)

    token = await create_session(db, shop_id)
    return AuthResponse(token=token, shop=ShopResponse(**shop_dict))


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: ShopLogin, db: aiosqlite.Connection = Depends(get_db)):
    """Log in with username and password, returning an active session token."""
    cursor = await db.execute(
        "SELECT id, username, password_hash, shop_name, owner_name, phone, branch, address, created_at FROM shops WHERE LOWER(username) = LOWER(?)",
        (body.username.strip(),),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    shop_dict = dict(row)
    stored_hash = shop_dict.pop("password_hash")

    if not verify_password(body.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = await create_session(db, shop_dict["id"])
    return AuthResponse(token=token, shop=ShopResponse(**shop_dict))


@router.get("/me", response_model=ShopResponse)
async def get_me(current_shop: dict = Depends(get_current_shop)):
    """Return currently logged-in shop profile."""
    return ShopResponse(**current_shop)


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Change the shopkeeper's password after verifying their current password."""
    shop_id = current_shop["id"]
    cursor = await db.execute("SELECT password_hash FROM shops WHERE id = ?", (shop_id,))
    row = await cursor.fetchone()
    if not row or not verify_password(body.current_password, row[0]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    # Extract current session token from authorization header to preserve it
    current_token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            current_token = parts[1]

    new_hash = hash_password(body.new_password)
    await db.execute("UPDATE shops SET password_hash = ? WHERE id = ?", (new_hash, shop_id))
    # Revoke all other active sessions for that shop, keeping current session
    await revoke_other_sessions(db, shop_id, keep_token=current_token)
    await db.commit()
    return {"success": True, "message": "Password changed successfully."}


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Log out and revoke current session token."""
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            await delete_session(db, parts[1])
    return {"success": True, "message": "Successfully logged out."}
