"""
backend/services/limiter.py
----------------------------
Rate limiting service using slowapi.
Provides a shared Limiter instance for route protection across FastAPI routers.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
