"""
backend/routers/customers.py
----------------------------
Customer directory and profile management endpoints for Bolti Slip.
All endpoints are strictly isolated by current_shop['id'].

Routes:
GET    /api/customers        — List/search shop customers
POST   /api/customers        — Create a new customer profile
GET    /api/customers/{id}   — Get customer details with their repair history
PATCH  /api/customers/{id}   — Update customer contact or notes
"""

from __future__ import annotations

from typing import List, Optional
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.database.db import get_db
from backend.models.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from backend.models.ticket import TicketResponse
from backend.services.auth import get_current_shop

router = APIRouter(prefix="/api/customers", tags=["customers"])


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    q: Optional[str] = Query(None, description="Search by customer name or phone number"),
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """List all customers belonging to the logged-in shop, with optional search query."""
    shop_id = current_shop["id"]

    query = """
        SELECT c.id, c.shop_id, c.name, c.phone, c.alternate_phone, c.email, c.notes,
               c.created_at, c.updated_at,
               COUNT(t.id) AS total_tickets
        FROM customers c
        LEFT JOIN tickets t ON t.customer_id = c.id
        WHERE c.shop_id = ?
    """
    params = [shop_id]

    if q and q.strip():
        search = f"%{q.strip()}%"
        query += " AND (c.name LIKE ? OR c.phone LIKE ?)"
        params.extend([search, search])

    query += " GROUP BY c.id ORDER BY c.updated_at DESC"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreate,
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Create a new customer under the current shop, or return existing if phone matches."""
    shop_id = current_shop["id"]
    clean_phone = body.phone.strip()

    # Check if customer already exists for this shop & phone
    cursor = await db.execute(
        "SELECT * FROM customers WHERE shop_id = ? AND phone = ?",
        (shop_id, clean_phone),
    )
    existing = await cursor.fetchone()
    if existing:
        cust_dict = _row_to_dict(existing)
        cust_dict["total_tickets"] = 0
        return cust_dict

    cursor = await db.execute(
        """
        INSERT INTO customers (shop_id, name, phone, alternate_phone, email, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            shop_id,
            body.name.strip(),
            clean_phone,
            body.alternate_phone.strip() if body.alternate_phone else None,
            body.email.strip() if body.email else None,
            body.notes.strip() if body.notes else None,
        ),
    )
    await db.commit()
    cust_id = cursor.lastrowid

    cursor = await db.execute("SELECT * FROM customers WHERE id = ?", (cust_id,))
    row = await cursor.fetchone()
    cust_dict = _row_to_dict(row)
    cust_dict["total_tickets"] = 0
    return cust_dict


@router.get("/{customer_id}")
async def get_customer_details(
    customer_id: int,
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get customer profile along with their full ticket repair history."""
    shop_id = current_shop["id"]

    cursor = await db.execute(
        "SELECT * FROM customers WHERE id = ? AND shop_id = ?",
        (customer_id, shop_id),
    )
    cust_row = await cursor.fetchone()
    if not cust_row:
        raise HTTPException(status_code=404, detail="Customer not found.")

    cust_dict = _row_to_dict(cust_row)

    # Fetch all tickets for this customer
    t_cursor = await db.execute(
        "SELECT * FROM tickets WHERE customer_id = ? AND shop_id = ? ORDER BY id DESC",
        (customer_id, shop_id),
    )
    ticket_rows = await t_cursor.fetchall()
    cust_dict["tickets"] = [_row_to_dict(r) for r in ticket_rows]
    cust_dict["total_tickets"] = len(ticket_rows)

    return cust_dict


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update customer details."""
    shop_id = current_shop["id"]

    cursor = await db.execute(
        "SELECT * FROM customers WHERE id = ? AND shop_id = ?",
        (customer_id, shop_id),
    )
    existing = await cursor.fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Customer not found.")

    updates = []
    params = []
    if body.name is not None:
        updates.append("name = ?")
        params.append(body.name.strip())
    if body.phone is not None:
        updates.append("phone = ?")
        params.append(body.phone.strip())
    if body.alternate_phone is not None:
        updates.append("alternate_phone = ?")
        params.append(body.alternate_phone.strip() if body.alternate_phone else None)
    if body.email is not None:
        updates.append("email = ?")
        params.append(body.email.strip() if body.email else None)
    if body.notes is not None:
        updates.append("notes = ?")
        params.append(body.notes.strip() if body.notes else None)

    if updates:
        params.extend([customer_id, shop_id])
        await db.execute(
            f"UPDATE customers SET {', '.join(updates)} WHERE id = ? AND shop_id = ?",
            params,
        )
        await db.commit()

    cursor = await db.execute(
        """
        SELECT c.*, COUNT(t.id) as total_tickets
        FROM customers c
        LEFT JOIN tickets t ON t.customer_id = c.id
        WHERE c.id = ? AND c.shop_id = ?
        GROUP BY c.id
        """,
        (customer_id, shop_id),
    )
    row = await cursor.fetchone()
    return _row_to_dict(row)
