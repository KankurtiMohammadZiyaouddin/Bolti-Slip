"""
backend/models/ticket.py
------------------------
Pydantic v2 schemas for the tickets resource.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Valid ticket statuses
TicketStatus = Literal["open", "in_progress", "resolved", "closed"]


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class TicketCreate(BaseModel):
    """Body expected by POST /api/tickets."""
    customer_name:       Optional[str]   = Field(None, max_length=120)
    customer_phone:      Optional[str]   = Field(None, max_length=20)
    device_description:  str             = Field(...,  min_length=1, max_length=2000)
    transcript_raw:      Optional[str]   = Field(None, max_length=4000)
    reported_problem:    Optional[str]   = Field(None, max_length=2000)
    repair_instructions: Optional[str]   = Field(None, max_length=2000)
    expected_delivery:   Optional[str]   = Field(None, max_length=30)   # ISO date string e.g. 2025-12-31
    estimated_cost:      Optional[float] = Field(None, ge=0)


class TicketStatusUpdate(BaseModel):
    """Body expected by PATCH /api/tickets/{id}/status."""
    status: TicketStatus


class SpeakRequest(BaseModel):
    """Body expected by POST /api/speak."""
    text:     str           = Field(..., min_length=1, max_length=2000)
    voice:    str           = Field("Devansh", max_length=50)
    language: str           = Field("hi-IN",   max_length=10)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TicketResponse(BaseModel):
    """Shape of a ticket returned by the API."""
    id:                  int
    ticket_number:       str
    customer_name:       Optional[str]
    customer_phone:      Optional[str]
    device_description:  str
    transcript_raw:      Optional[str]
    reported_problem:    Optional[str]
    repair_instructions: Optional[str]
    expected_delivery:   Optional[str]
    estimated_cost:      Optional[float]
    status:              TicketStatus
    created_at:          str
    updated_at:          str
    shop_id:             Optional[int] = None
    customer_id:         Optional[int] = None

    model_config = {"from_attributes": True}


class TranscribeResponse(BaseModel):
    """Shape returned by POST /api/transcribe."""
    success:                 bool
    transcript:              Optional[str]
    detected_language_code:  Optional[str]
    model:                   str
    http_status_code:        Optional[int]
    api_processing_time:     Optional[float]
    request_elapsed_seconds: Optional[float]
    error:                   Optional[str]
    error_type:              Optional[str]


class HealthResponse(BaseModel):
    status: str
    version: str


# ---------------------------------------------------------------------------
# Extraction schemas
# ---------------------------------------------------------------------------

class ExtractRequest(BaseModel):
    """Body expected by POST /api/extract."""
    transcript: str = Field(..., min_length=1, max_length=4000)


class ExtractedFields(BaseModel):
    """Structured ticket fields extracted from a transcript."""
    customer_name:       Optional[str]   = None
    customer_phone:      Optional[str]   = None
    device_description:  Optional[str]   = None
    reported_problem:    Optional[str]   = None
    repair_instructions: Optional[str]   = None
    expected_delivery:   Optional[str]   = None
    estimated_cost:      Optional[float] = None
    transcript_raw:      Optional[str]   = None


class ExtractResponse(BaseModel):
    """Shape returned by POST /api/extract."""
    success:            bool
    fields:             ExtractedFields
    missing_fields:     list[str]
    needs_confirmation: list[str]
    unresolved_phrases: list[str]
