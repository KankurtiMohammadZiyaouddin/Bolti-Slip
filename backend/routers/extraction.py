"""
backend/routers/extraction.py
------------------------------
POST /api/extract — parse a repair-shop transcript into structured fields.

No external AI APIs are used.  Pure rule-based extraction via
backend.services.ticket_extractor.TicketExtractor.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.models.ticket import ExtractRequest, ExtractResponse, ExtractedFields
from backend.services.ticket_extractor import TicketExtractor

router = APIRouter(prefix="/api", tags=["extraction"])

_extractor = TicketExtractor()


@router.post("/extract", response_model=ExtractResponse)
def extract_ticket_fields(body: ExtractRequest) -> ExtractResponse:
    """
    Parse a voice transcript (Hindi / English / Hinglish) and return
    structured ticket fields.

    - Fields that cannot be found are **null** (never invented).
    - Ambiguous values (e.g. a named weekday for a delivery date) are
      returned in ``needs_confirmation``.
    - Text fragments that look meaningful but could not be mapped appear
      in ``unresolved_phrases``.
    """
    result = _extractor.extract(body.transcript)

    return ExtractResponse(
        success=result["success"],
        fields=ExtractedFields(**result["fields"]),
        missing_fields=result["missing_fields"],
        needs_confirmation=result["needs_confirmation"],
        unresolved_phrases=result["unresolved_phrases"],
    )
