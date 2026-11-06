"""
backend/routers/speech.py
--------------------------
TTS endpoints powered by Gnani Timbre v3.0.

Routes
------
POST /api/speak               — synthesise arbitrary text → WAV audio
POST /api/tickets/{id}/confirm — build a spoken confirmation for a ticket
"""

from __future__ import annotations

import asyncio

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from backend.database.db import get_db
from backend.models.ticket import SpeakRequest
from backend.services.timbre import TimbreService

router = APIRouter(prefix="/api", tags=["speech"])

# TimbreService reads GNANI_API_KEY_ID from backend/.env
_timbre = TimbreService()

_DEFAULT_VOICE    = "Devansh"
_DEFAULT_LANGUAGE = "hi-IN"


@router.post("/speak")
async def speak(body: SpeakRequest):
    """
    Synthesise text to WAV audio using Gnani Timbre v3.0.

    Returns the raw WAV bytes with Content-Type: audio/wav.
    Default voice: Devansh, language: hi-IN.
    """
    result = await asyncio.to_thread(
        _timbre.synthesise,
        body.text,
        voice=body.voice,
        language=body.language,
    )

    if not result["success"]:
        raise HTTPException(status_code=502, detail=result["error"])

    return Response(
        content=result["audio_bytes"],
        media_type="audio/wav",
        headers={"X-Audio-Size": str(result["audio_size_bytes"])},
    )


@router.post("/tickets/{ticket_id}/confirm")
async def confirm_ticket(
    ticket_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    Build a spoken Hindi confirmation for a ticket and return WAV audio.

    Reads the ticket from the database, constructs a confirmation sentence,
    synthesises it with Timbre v3.0 (voice=Devansh), and streams the WAV.
    """
    cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found.")

    ticket = dict(row)

    # Build confirmation sentence in Hindi
    parts = [f"आपका रिपेयर टिकट {ticket['ticket_number']} सफलतापूर्वक तैयार हो गया है।"]
    if ticket.get('customer_name'):
        parts.append(f"ग्राहक {ticket['customer_name']}।")
    parts.append(f"उपकरण: {ticket['device_description']}।")
    if ticket.get('reported_problem'):
        parts.append(f"समस्या: {ticket['reported_problem']}।")
    if ticket.get('estimated_cost'):
        parts.append(f"अनुमानित लागत: {ticket['estimated_cost']} रुपये।")
    if ticket.get('expected_delivery'):
        parts.append(f"अपेक्षित डिलीवरी: {ticket['expected_delivery']}।")
    parts.append("धन्यवाद!")
    confirmation_text = " ".join(parts)

    result = await asyncio.to_thread(
        _timbre.synthesise,
        confirmation_text,
        voice=_DEFAULT_VOICE,
        language=_DEFAULT_LANGUAGE,
    )

    if not result["success"]:
        raise HTTPException(status_code=502, detail=result["error"])

    return Response(
        content=result["audio_bytes"],
        media_type="audio/wav",
        headers={
            "X-Ticket-Number": ticket["ticket_number"],
            "X-Audio-Size":    str(result["audio_size_bytes"]),
        },
    )
