"""
backend/routers/tickets.py
--------------------------
CRUD endpoints for repair tickets.

Routes
------
POST   /api/tickets              — create a new ticket
GET    /api/tickets              — list all tickets (newest first)
GET    /api/tickets/{id}         — get a single ticket
PATCH  /api/tickets/{id}/status  — update ticket status
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.database.db import get_db
from backend.models.ticket import TicketCreate, TicketResponse, TicketStatusUpdate

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _next_ticket_number(db: aiosqlite.Connection) -> str:
    """Return the next BLT-XXXX number by counting existing rows."""
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
async def create_ticket(body: TicketCreate, db: aiosqlite.Connection = Depends(get_db)):
    """Create a new repair ticket."""
    ticket_number = await _next_ticket_number(db)

    await db.execute(
        """
        INSERT INTO tickets (ticket_number, customer_name, customer_phone,
                             device_description, transcript_raw,
                             reported_problem, repair_instructions,
                             expected_delivery, estimated_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_number,
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
        "SELECT * FROM tickets WHERE ticket_number = ?", (ticket_number,)
    )
    row = await cursor.fetchone()
    return _row_to_dict(row)


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """List all tickets, newest first. Optionally filter by status."""
    if status:
        cursor = await db.execute(
            "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC", (status,)
        )
    else:
        cursor = await db.execute("SELECT * FROM tickets ORDER BY id DESC")

    rows = await cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """Get a single ticket by its numeric ID."""
    cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")
    return _row_to_dict(row)


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: int,
    body: TicketStatusUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    """Update a ticket's status (open → in_progress → resolved → closed)."""
    cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    await db.execute(
        "UPDATE tickets SET status = ? WHERE id = ?", (body.status, ticket_id)
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = await cursor.fetchone()
    return _row_to_dict(row)
