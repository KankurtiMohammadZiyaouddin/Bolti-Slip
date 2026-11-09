"""
backend/models/auth.py
----------------------
Pydantic v2 schemas for authentication, shopkeepers, and sessions.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ShopRegister(BaseModel):
    """Payload for POST /api/auth/register."""
    username:   str           = Field(..., min_length=3, max_length=50, description="Login handle, case-insensitive")
    password:   str           = Field(..., min_length=6, max_length=128, description="Plaintext password")
    shop_name:  str           = Field(..., min_length=1, max_length=120, description="e.g. Sharma Electronics")
    owner_name: str           = Field(..., min_length=1, max_length=120, description="e.g. Rajesh Sharma")
    phone:      Optional[str] = Field(None, max_length=20, description="Shop contact phone")
    branch:     Optional[str] = Field("Main Branch", max_length=100, description="e.g. Pune Main Branch")
    address:    Optional[str] = Field(None, max_length=255, description="Physical shop address")


class ShopLogin(BaseModel):
    """Payload for POST /api/auth/login."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class ShopResponse(BaseModel):
    """Safe public shop profile."""
    id:         int
    username:   str
    shop_name:  str
    owner_name: str
    phone:      Optional[str] = None
    branch:     Optional[str] = None
    address:    Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Response returned upon successful registration or login."""
    token: str
    shop:  ShopResponse


class PasswordChangeRequest(BaseModel):
    """Payload for POST /api/auth/change-password."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password:     str = Field(..., min_length=6, max_length=128)
