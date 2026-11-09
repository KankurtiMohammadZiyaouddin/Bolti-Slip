"""
backend/database/backup.py
--------------------------
Automated, reliable SQLite database backup and retention management for Bolti Slip.
Uses Python's native sqlite3 Connection.backup() API to create consistent online snapshots
without taking the database offline or blocking concurrent readers.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from backend.config import get_backup_dir, get_backup_retention_days

logger = logging.getLogger(__name__)

# Backup filename pattern: bolti_slip_backup_YYYYMMDD_HHMMSS_{pid}.db (with optional microsecond/counter)
# Supports legacy format without pid for backward compatibility with existing backups.
BACKUP_FILENAME_REGEX = re.compile(r"^bolti_slip_backup_\d{8}_\d{6}(?:_\d+)*\.db$")

# State to prevent redundant duplicate backups within the same process execution
_last_backup_time: float = 0.0
_last_backup_path: Optional[Path] = None
MIN_BACKUP_INTERVAL_SECONDS: int = 300  # 5 minutes


def run_backup_retention(
    backup_dir: Path,
    retention_days: int,
    source_db_path: Path,
) -> List[Path]:
    """
    Remove expired database backups exceeding the retention threshold.

    Safety Rules:
    - Only removes files strictly matching BACKUP_FILENAME_REGEX.
    - NEVER touches the live database, even if placed in the backup directory.
    - NEVER touches unrelated files (e.g. logs, .txt, scripts, other .db files).
    - Safely handles missing directory.
    """
    if not backup_dir.exists() or not backup_dir.is_dir():
        return []

    removed_files: List[Path] = []
    now = time.time()
    cutoff_age_seconds = retention_days * 86400.0

    try:
        resolved_source = source_db_path.resolve() if source_db_path.exists() else None

        for item in backup_dir.iterdir():
            if not item.is_file():
                continue

            # Must match exact backup filename convention
            if not BACKUP_FILENAME_REGEX.match(item.name):
                continue

            # Critical Safety: Never delete the active live database
            if resolved_source and item.resolve() == resolved_source:
                continue

            try:
                file_age_seconds = now - item.stat().st_mtime
                if file_age_seconds > cutoff_age_seconds:
                    item.unlink()
                    removed_files.append(item)
                    logger.info(
                        "Removed expired database backup: %s (age: %.1f days, retention limit: %d days)",
                        item.name,
                        file_age_seconds / 86400.0,
                        retention_days,
                    )
            except Exception as e:
                logger.warning("Could not remove expired backup file '%s': %s", item.name, e)

    except Exception as e:
        logger.error("Error running backup retention cleanup in '%s': %s", backup_dir, e)

    return removed_files


def create_backup(
    source_db_path: Path | str | None = None,
    backup_dir: Path | str | None = None,
    retention_days: int | None = None,
    force: bool = False,
) -> Optional[Path]:
    """
    Create a consistent online snapshot of the SQLite database using Connection.backup().

    Parameters:
    - source_db_path: Path to live SQLite database (defaults to bolti_slip.db).
    - backup_dir: Destination directory for backup file (defaults to get_backup_dir()).
    - retention_days: Days to retain backups before removal (defaults to get_backup_retention_days()).
    - force: If True, bypasses the debounce / duplicate prevention check.

    Returns:
    - Path to the newly created backup file on success, or None on failure / skip.
    """
    global _last_backup_time, _last_backup_path

    # Resolve source database path
    if source_db_path is None:
        from backend.database.db import _DB_PATH
        source_db_path = _DB_PATH
    source_path = Path(source_db_path).resolve()

    if not source_path.exists() or source_path.stat().st_size == 0:
        logger.debug("Source database '%s' does not exist or is empty; skipping backup.", source_path)
        return None

    # Debounce / Duplicate Prevention: Avoid creating multiple backups during repeated startups
    now = time.time()
    if not force and _last_backup_path and (now - _last_backup_time < MIN_BACKUP_INTERVAL_SECONDS):
        logger.debug(
            "Skipping duplicate backup: A recent backup was created %.1f seconds ago at '%s'",
            now - _last_backup_time,
            _last_backup_path.name,
        )
        return _last_backup_path

    # Resolve backup directory and retention settings
    dest_dir = Path(backup_dir).resolve() if backup_dir else get_backup_dir()
    retention = retention_days if retention_days is not None else get_backup_retention_days()

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Format timestamped backup filename with process ID for worker uniqueness
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    pid = os.getpid()
    target_name = f"bolti_slip_backup_{timestamp_str}_{pid}.db"
    target_path = dest_dir / target_name

    # If file exists (same second + same PID), append microsecond suffix
    if target_path.exists():
        micro_str = f"{datetime.now(timezone.utc).microsecond:06d}"
        target_name = f"bolti_slip_backup_{timestamp_str}_{pid}_{micro_str}.db"
        target_path = dest_dir / target_name

    try:
        # Perform consistent online backup using SQLite's native backup API
        src_conn = sqlite3.connect(source_path)
        dst_conn = sqlite3.connect(target_path)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()

        # Verify backup integrity (exists and has non-zero size)
        if not target_path.exists() or target_path.stat().st_size == 0:
            raise IOError("Backup destination file is missing or zero bytes after backup operation.")

        _last_backup_time = now
        _last_backup_path = target_path

        logger.info(
            "Successfully created database backup: %s (%d bytes)",
            target_path.name,
            target_path.stat().st_size,
        )

        # Apply retention cleanup
        run_backup_retention(
            backup_dir=dest_dir,
            retention_days=retention,
            source_db_path=source_path,
        )

        return target_path

    except Exception as e:
        logger.error("Failed to create database backup: %s", str(e))
        # Clean up incomplete or corrupted backup file
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception:
                pass
        return None
