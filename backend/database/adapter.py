"""
backend/database/adapter.py
----------------------------
Multi-engine async database abstraction layer for Bolti Slip.
Supports both SQLite (via aiosqlite) and PostgreSQL (via asyncpg).

Architecture Rules:
- Default engine is SQLite for local development and test isolation.
- Automatically selects PostgreSQL when DATABASE_URL is configured (starts with postgresql:// or postgres://).
- Provides a unified DatabaseConnection interface supporting:
    cursor = await db.execute(sql, params)
    await db.commit()
    await db.rollback()
    row = await cursor.fetchone()
    rows = await cursor.fetchall()
    dict(row), row["col"], row[0], row.get("col")
    cursor.lastrowid
- Uses safe, token-based placeholder conversion (? -> $1, $2, ...) without corrupting string literals or comments.
- Supports INSERT ... RETURNING id on PostgreSQL to transparently populate cursor.lastrowid.
- Never logs or exposes database credentials.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


def mask_database_url(url: Optional[str]) -> str:
    """Mask password and credentials in a database URL for safe logging."""
    if not url:
        return "[NOT SET]"
    try:
        parsed = urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username or ''}:***@{parsed.hostname or ''}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse(parsed._replace(netloc=netloc))
        return urlunparse(parsed)
    except Exception:
        return "postgresql://***:***@.../..."


def sanitize_sql_for_postgres(sql: str) -> str:
    """
    Sanitize SQLite-specific syntax for PostgreSQL execution without altering
    query semantics:
    - Rewrites 'column = ? COLLATE NOCASE' to 'LOWER(column) = LOWER(?)'
    - Strips any remaining standalone 'COLLATE NOCASE' clauses
    """
    # Rewrite 'col = ? COLLATE NOCASE' to 'LOWER(col) = LOWER(?)'
    pattern = re.compile(r"(\b\w+)\s*=\s*\?\s+COLLATE\s+NOCASE", re.IGNORECASE)
    sanitized = pattern.sub(r"LOWER(\1) = LOWER(?)", sql)
    # Strip any remaining standalone COLLATE NOCASE
    sanitized = re.sub(r"\s+COLLATE\s+NOCASE", "", sanitized, flags=re.IGNORECASE)
    return sanitized


def get_database_engine() -> str:
    """
    Determine the active database engine from environment.
    Returns 'postgres' if DATABASE_URL starts with postgresql:// or postgres://.
    Otherwise returns 'sqlite'.
    """
    raw_url = os.getenv("DATABASE_URL", "").strip()
    if raw_url.startswith("postgresql://") or raw_url.startswith("postgres://"):
        return "postgres"
    return "sqlite"


def normalize_param_for_postgres(val: Any) -> Any:
    """
    Ensure parameters passed to PostgreSQL prepared statements match column types.
    Parses ISO 8601 strings to datetime objects for TIMESTAMPTZ columns.
    Converts float values to Decimal for NUMERIC columns.
    """
    if isinstance(val, float):
        return Decimal(str(val))
    if isinstance(val, str) and len(val) >= 19 and "T" in val:
        try:
            return datetime.fromisoformat(val)
        except (ValueError, TypeError):
            return val
    return val


def convert_qmark_to_dollar(sql: str) -> str:
    """
    Safely converts SQLite '?' positional placeholders to PostgreSQL '$1, $2, ...' placeholders.

    Scanner state machine rules:
    - Never converts '?' inside single-quoted string literals ('...').
    - Handles escaped single quotes ('' inside string).
    - Never converts '?' inside double-quoted identifiers ("...").
    - Never converts '?' inside line comments (-- ...) or block comments (/* ... */).
    - Numbering is sequential starting at $1.
    """
    out: List[str] = []
    param_idx = 1
    i = 0
    n = len(sql)
    state = "NORMAL"

    while i < n:
        ch = sql[i]
        if state == "NORMAL":
            if ch == "'":
                state = "SINGLE_QUOTE"
                out.append(ch)
            elif ch == '"':
                state = "DOUBLE_QUOTE"
                out.append(ch)
            elif ch == "-" and i + 1 < n and sql[i + 1] == "-":
                state = "LINE_COMMENT"
                out.append("--")
                i += 1
            elif ch == "/" and i + 1 < n and sql[i + 1] == "*":
                state = "BLOCK_COMMENT"
                out.append("/*")
                i += 1
            elif ch == "?":
                out.append(f"${param_idx}")
                param_idx += 1
            else:
                out.append(ch)
        elif state == "SINGLE_QUOTE":
            out.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("'")
                    i += 1
                else:
                    state = "NORMAL"
        elif state == "DOUBLE_QUOTE":
            out.append(ch)
            if ch == '"':
                if i + 1 < n and sql[i + 1] == '"':
                    out.append('"')
                    i += 1
                else:
                    state = "NORMAL"
        elif state == "LINE_COMMENT":
            out.append(ch)
            if ch == "\n":
                state = "NORMAL"
        elif state == "BLOCK_COMMENT":
            out.append(ch)
            if ch == "*" and i + 1 < n and sql[i + 1] == "/":
                out.append("/")
                i += 1
                state = "NORMAL"
        i += 1

    return "".join(out)


class RowWrapper(Mapping[str, Any]):
    """
    Unified row wrapper providing dictionary, attribute, index and mapping access.
    Compatible with aiosqlite.Row, sqlite3.Row, and asyncpg.Record.
    Serializes datetimes to ISO 8601 strings when accessed as dict values to preserve
    compatibility with existing Pydantic ticket/customer/shop models.
    """

    def __init__(self, data: Union[Mapping[str, Any], Sequence[Any], Any], keys: Optional[Sequence[str]] = None):
        if hasattr(data, "keys") and callable(data.keys):
            # Handles sqlite3.Row, aiosqlite.Row, asyncpg.Record, and dict-like mappings
            self._keys = list(data.keys())
            self._values = [data[k] for k in self._keys]
            self._dict = dict(zip(self._keys, self._values))
        elif isinstance(data, Mapping):
            self._dict = dict(data)
            self._keys = list(data.keys())
            self._values = list(data.values())
        elif keys is not None:
            self._keys = list(keys)
            self._values = list(data)
            self._dict = dict(zip(self._keys, self._values))
        else:
            # Fallback for plain tuple/sequence without column names
            self._keys = [f"col_{i}" for i in range(len(data))]
            self._values = list(data)
            self._dict = dict(zip(self._keys, self._values))

        # Format datetimes to ISO 8601 strings and Decimals to floats in dictionary representation
        for k, v in self._dict.items():
            if isinstance(v, (datetime, date)):
                self._dict[k] = v.isoformat()
            elif isinstance(v, Decimal):
                self._dict[k] = float(v)

    def __getitem__(self, key: Union[str, int]) -> Any:
        if isinstance(key, int):
            return self._values[key]
        return self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)

    def __contains__(self, key: object) -> bool:
        return key in self._dict

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def get(self, key: str, default: Any = None) -> Any:
        return self._dict.get(key, default)

    def __repr__(self) -> str:
        return f"RowWrapper({self._dict})"


class CursorWrapper:
    """
    Unified cursor wrapper providing fetchone(), fetchall(), lastrowid, and rowcount.
    """

    def __init__(
        self,
        rows: Optional[List[RowWrapper]] = None,
        lastrowid: Optional[int] = None,
        rowcount: int = 0,
    ):
        self._rows: List[RowWrapper] = rows or []
        self._index = 0
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    async def fetchone(self) -> Optional[RowWrapper]:
        if self._index < len(self._rows):
            row = self._rows[self._index]
            self._index += 1
            return row
        return None

    async def fetchall(self) -> List[RowWrapper]:
        remaining = self._rows[self._index :]
        self._index = len(self._rows)
        return remaining


class SqliteConnectionWrapper:
    """
    Wraps an aiosqlite.Connection providing the unified DatabaseConnection interface.
    """

    def __init__(self, conn: Any):
        self._conn = conn

    async def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Any:
        if params is not None:
            cur = await self._conn.execute(sql, tuple(params))
        else:
            cur = await self._conn.execute(sql)

        # Wrap cursor so row behaviors (dict, keys, index) are consistent
        raw_rows = await cur.fetchall()
        rows = [RowWrapper(r) for r in raw_rows] if raw_rows else []
        return CursorWrapper(rows=rows, lastrowid=cur.lastrowid, rowcount=cur.rowcount)

    async def commit(self) -> None:
        await self._conn.commit()

    async def rollback(self) -> None:
        await self._conn.rollback()

    async def close(self) -> None:
        await self._conn.close()

    @property
    def raw_connection(self) -> Any:
        return self._conn


class PostgresConnectionWrapper:
    """
    Wraps an asyncpg.Connection providing the unified DatabaseConnection interface.
    Translates '?' placeholders, manages explicit transactions, and handles 'RETURNING id'.
    """

    def __init__(self, conn: Any, transaction: Optional[Any] = None):
        self._conn = conn
        self._transaction = transaction
        self._in_transaction = False

    async def _ensure_transaction(self):
        if not self._in_transaction:
            self._transaction = self._conn.transaction()
            await self._transaction.start()
            self._in_transaction = True

    async def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> CursorWrapper:
        # 1. Sanitize query and handle SQLite-specific clauses (e.g. COLLATE NOCASE)
        cleaned_sql = sanitize_sql_for_postgres(sql)

        # 2. Check if INSERT requires lastrowid capture via RETURNING id
        is_insert = cleaned_sql.strip().upper().startswith("INSERT INTO")
        needs_returning = is_insert and ("RETURNING" not in cleaned_sql.upper())

        if needs_returning:
            # Append RETURNING id to capture generated primary key
            exec_sql = cleaned_sql.rstrip().rstrip(";") + " RETURNING id;"
        else:
            exec_sql = cleaned_sql

        # 3. Convert '?' to '$1, $2, ...' and normalize parameter types
        pg_sql = convert_qmark_to_dollar(exec_sql)
        pg_params = (
            tuple(normalize_param_for_postgres(p) for p in params) if params is not None else ()
        )

        # 4. Determine if query returns rows
        is_query_with_return = (
            pg_sql.strip().upper().startswith("SELECT")
            or "RETURNING" in pg_sql.upper()
            or pg_sql.strip().upper().startswith("WITH")
        )

        lastrowid: Optional[int] = None
        rowcount = 0
        wrapped_rows: List[RowWrapper] = []

        if is_query_with_return:
            records = await self._conn.fetch(pg_sql, *pg_params)
            for rec in records:
                row_dict = dict(rec)
                wrapped_rows.append(RowWrapper(row_dict))
                # Capture generated id if returning clause added
                if needs_returning and "id" in row_dict:
                    lastrowid = row_dict["id"]
            rowcount = len(records)
        else:
            status = await self._conn.execute(pg_sql, *pg_params)
            # Parse rowcount from command tag (e.g. 'UPDATE 1', 'DELETE 2')
            try:
                parts = status.split()
                if parts and parts[-1].isdigit():
                    rowcount = int(parts[-1])
            except Exception:
                rowcount = 0

        return CursorWrapper(rows=wrapped_rows, lastrowid=lastrowid, rowcount=rowcount)

    async def commit(self) -> None:
        if self._in_transaction and self._transaction:
            await self._transaction.commit()
            self._in_transaction = False
            self._transaction = None

    async def rollback(self) -> None:
        if self._in_transaction and self._transaction:
            await self._transaction.rollback()
            self._in_transaction = False
            self._transaction = None

    async def close(self) -> None:
        if self._in_transaction and self._transaction:
            try:
                await self._transaction.rollback()
            except Exception:
                pass
            self._in_transaction = False
        # Do not close pool connection directly; return to pool handled by caller

    @property
    def raw_connection(self) -> Any:
        return self._conn
