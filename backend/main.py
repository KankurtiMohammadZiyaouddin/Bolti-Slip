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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.db import init_db
from backend.models.ticket import HealthResponse
from backend.routers import transcription, tickets, speech, extraction


# ---------------------------------------------------------------------------
# Lifespan — runs init_db() once before accepting requests
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Bolti Slip API",
    description="Voice-powered repair ticket management — Gnani Prisma STT + Timbre TTS",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the Vite dev server (port 5173) and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(transcription.router)
app.include_router(tickets.router)
app.include_router(speech.router)
app.include_router(extraction.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health():
    """Simple liveness check — returns 200 when the API is running."""
    return {"status": "ok", "version": "1.0.0"}
