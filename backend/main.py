"""
backend/main.py
---------------
Bolti Slip — FastAPI application entry point.

Start the server:
    cd C:\\Programs\\Project\\Bolti-Slip
    .venv\\Scripts\\Activate.ps1
    pip install -r backend/requirements.txt
    uvicorn backend.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# Ensure root .env and backend/.env are loaded without overriding existing deployment env vars
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from backend.config import get_cors_settings
from backend.database.adapter import get_database_engine
from backend.database.backup import create_backup
from backend.database.db import close_db, init_db
from backend.models.ticket import HealthResponse
from backend.routers import transcription, tickets, speech, extraction, auth, customers
from backend.services.limiter import limiter


# ---------------------------------------------------------------------------
# Lifespan — runs init_db() and automated database backup on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if get_database_engine() == "sqlite":
        create_backup()
    yield
    await close_db()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Bolti Slip API",
    description="Voice-powered repair ticket management — Gnani Prisma STT + Timbre TTS",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting state and handler
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )

# Production CORS configuration based on environment settings
cors_settings = get_cors_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings["allow_origins"],
    allow_credentials=cors_settings["allow_credentials"],
    allow_methods=cors_settings["allow_methods"],
    allow_headers=cors_settings["allow_headers"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(transcription.router)
app.include_router(tickets.router)
app.include_router(speech.router)
app.include_router(extraction.router)
app.include_router(auth.router)
app.include_router(customers.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health():
    """Simple liveness check — returns 200 when the API is running."""
    return {"status": "ok", "version": "1.0.0"}
