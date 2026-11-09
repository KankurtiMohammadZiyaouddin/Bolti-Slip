"""
backend/models/customer.py
--------------------------
Pydantic v2 schemas for customer directory and customer profiles.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    """Payload for POST /api/customers."""
    name:            str           = Field(..., min_length=1, max_length=120)
    phone:           str           = Field(..., min_length=5, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    email:           Optional[str] = Field(None, max_length=120)
    notes:           Optional[str] = Field(None, max_length=1000)


class CustomerUpdate(BaseModel):
    """Payload for PATCH /api/customers/{id}."""
    name:            Optional[str] = Field(None, min_length=1, max_length=120)
    phone:           Optional[str] = Field(None, min_length=5, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    email:           Optional[str] = Field(None, max_length=120)
    notes:           Optional[str] = Field(None, max_length=1000)


class CustomerResponse(BaseModel):
    """Customer profile returned by API."""
    id:              int
    shop_id:         int
    name:            str
    phone:           str
    alternate_phone: Optional[str] = None
    email:           Optional[str] = None
    notes:           Optional[str] = None
    created_at:      str
    updated_at:      str
    total_tickets:   Optional[int] = 0

    model_config = {"from_attributes": True}
