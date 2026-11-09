"""
backend/config.py
-----------------
Application configuration and security settings for Bolti Slip.
Manages:
- Environment mode (development vs production)
- Production CORS origin parsing and restrictions
- Automated SQLite database backup directory and retention settings
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Project root directory: C:\Programs\Project\Bolti-Slip
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default development origins for Vite dev server & local frontend testing
DEFAULT_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Standard allowed HTTP methods and headers for Bolti Slip API
ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = ["Authorization", "Content-Type", "Accept", "X-Requested-With"]


def is_production_mode() -> bool:
    """Check if application is running in production mode via environment variable."""
    env_str = os.getenv("BOLTI_ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    return env_str in ("production", "prod")


def get_backup_dir() -> Path:
    """Return the configured backup directory path, ensuring it exists."""
    custom_dir = os.getenv("BOLTI_BACKUP_DIR")
    if custom_dir and custom_dir.strip():
        backup_path = Path(custom_dir.strip())
        if not backup_path.is_absolute():
            backup_path = PROJECT_ROOT / backup_path
    else:
        backup_path = PROJECT_ROOT / "backups"

    try:
        backup_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error("Failed to create backup directory '%s': %s", backup_path, e)

    return backup_path.resolve()


def get_backup_retention_days() -> int:
    """Return retention period for backups in days (minimum 1, default 30)."""
    raw_days = os.getenv("BOLTI_BACKUP_RETENTION_DAYS", "30")
    try:
        days = int(raw_days.strip())
        return max(1, days)
    except (ValueError, AttributeError):
        return 30


def parse_cors_origins(raw_origins: str | None, is_production: bool) -> List[str]:
    """
    Parse and validate CORS origins from environment configuration.

    Rules:
    - Multiple origins are separated by commas.
    - Each origin is trimmed and trailing slashes are removed.
    - Origins must specify a valid http:// or https:// scheme.
    - Wildcard '*' is strictly forbidden in production mode and will be discarded.
    - In development mode, localhost origins are automatically included.
    - In production mode, if no valid origins are configured, an empty list is returned
      and a warning is logged so cross-origin requests fail safely.
    """
    origins: List[str] = []

    if raw_origins:
        for entry in raw_origins.split(","):
            cleaned = entry.strip()
            if not cleaned:
                continue

            if cleaned == "*":
                if is_production:
                    logger.warning(
                        "CORS SECURITY WARNING: Wildcard '*' origin is disallowed in production mode. "
                        "Origin ignored."
                    )
                else:
                    if "*" not in origins:
                        origins.append("*")
                continue

            # Must start with http:// or https://
            if cleaned.startswith("http://") or cleaned.startswith("https://"):
                normalized = cleaned.rstrip("/")
                if normalized not in origins:
                    origins.append(normalized)
            else:
                logger.warning(
                    "CORS configuration warning: Skipping invalid origin (must start with http:// or https://): '%s'",
                    cleaned,
                )

    if not is_production:
        # Development mode: Include default localhost origins
        for dev_origin in DEFAULT_DEV_ORIGINS:
            if dev_origin not in origins and "*" not in origins:
                origins.append(dev_origin)
    else:
        # Production mode: If no origins defined, warn loudly
        if not origins:
            logger.warning(
                "CORS SECURITY ALERT: Running in PRODUCTION mode with no valid origins configured in BOLTI_CORS_ORIGINS. "
                "All cross-origin browser requests will be blocked."
            )

    return origins


def get_cors_settings() -> dict:
    """Return dictionary of arguments for FastAPI CORSMiddleware."""
    in_prod = is_production_mode()
    raw = os.getenv("BOLTI_CORS_ORIGINS")
    allowed_origins = parse_cors_origins(raw, in_prod)

    # Enable credentials only when specific origins are configured (never with wildcard)
    has_origins = len(allowed_origins) > 0
    allow_credentials = has_origins and ("*" not in allowed_origins)

    return {
        "allow_origins": allowed_origins,
        "allow_credentials": allow_credentials,
        "allow_methods": ALLOWED_METHODS,
        "allow_headers": ALLOWED_HEADERS,
    }
