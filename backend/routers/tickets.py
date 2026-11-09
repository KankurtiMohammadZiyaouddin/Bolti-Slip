"""
backend/routers/tickets.py
--------------------------
CRUD endpoints for repair tickets with multi-shop isolation and customer linking.

Routes
------
POST   /api/tickets              — create a new ticket (scoped to current shop)
GET    /api/tickets              — list current shop's tickets (newest first)
GET    /api/tickets/{id}         — get a single ticket for current shop
PATCH  /api/tickets/{id}/status  — update ticket status for current shop
"""

from __future__ import annotations

from typing import List, Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.database.db import get_db
from backend.models.ticket import TicketCreate, TicketResponse, TicketStatusUpdate
from backend.services.auth import get_current_shop

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _next_ticket_number(db: aiosqlite.Connection) -> str:
    """Return the next global BLT-XXXX number by counting existing rows."""
    cursor = await db.execute("SELECT COUNT(*) FROM tickets")
    row = await cursor.fetchone()
    n = (row[0] if row else 0) + 1
    return f"BLT-{n:04d}"


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreate,
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Create a new repair ticket under the logged-in shop and auto-link customer."""
    shop_id = current_shop["id"]
    ticket_number = await _next_ticket_number(db)

    # Auto-resolve or create customer profile under this shop
    customer_id = None
    if body.customer_phone and body.customer_phone.strip():
        phone_clean = body.customer_phone.strip()
        cursor = await db.execute(
            "SELECT id FROM customers WHERE shop_id = ? AND phone = ?",
            (shop_id, phone_clean),
        )
        cust_row = await cursor.fetchone()
        if cust_row:
            customer_id = cust_row[0]
        else:
            cust_name = body.customer_name.strip() if body.customer_name and body.customer_name.strip() else "Valued Customer"
            cur_ins = await db.execute(
                """
                INSERT INTO customers (shop_id, name, phone)
                VALUES (?, ?, ?)
                """,
                (shop_id, cust_name, phone_clean),
            )
            customer_id = cur_ins.lastrowid

    await db.execute(
        """
        INSERT INTO tickets (ticket_number, shop_id, customer_id, customer_name, customer_phone,
                             device_description, transcript_raw,
                             reported_problem, repair_instructions,
                             expected_delivery, estimated_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_number,
            shop_id,
            customer_id,
            body.customer_name,
            body.customer_phone,
            body.device_description,
            body.transcript_raw,
            body.reported_problem,
            body.repair_instructions,
            body.expected_delivery,
            body.estimated_cost,
        ),
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT * FROM tickets WHERE ticket_number = ? AND shop_id = ?",
        (ticket_number, shop_id),
    )
    row = await cursor.fetchone()
    return _row_to_dict(row)


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """List all tickets belonging to the logged-in shop, newest first. Optionally filter by status."""
    shop_id = current_shop["id"]
    if status:
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE shop_id = ? AND status = ? ORDER BY id DESC",
            (shop_id, status),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE shop_id = ? ORDER BY id DESC",
            (shop_id,),
        )

    rows = await cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Get a single ticket by ID, scoped to the current shop."""
    shop_id = current_shop["id"]
    cursor = await db.execute(
        "SELECT * FROM tickets WHERE id = ? AND shop_id = ?",
        (ticket_id, shop_id),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")
    return _row_to_dict(row)


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: int,
    body: TicketStatusUpdate,
    current_shop: dict = Depends(get_current_shop),
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update a ticket's status (open → in_progress → resolved → closed) for current shop."""
    shop_id = current_shop["id"]
    cursor = await db.execute(
        "SELECT * FROM tickets WHERE id = ? AND shop_id = ?",
        (ticket_id, shop_id),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    await db.execute(
        "UPDATE tickets SET status = ? WHERE id = ? AND shop_id = ?",
        (body.status, ticket_id, shop_id),
    )
    await db.commit()

    cursor = await db.execute(
        "SELECT * FROM tickets WHERE id = ? AND shop_id = ?",
        (ticket_id, shop_id),
    )
    row = await cursor.fetchone()
    return _row_to_dict(row)
