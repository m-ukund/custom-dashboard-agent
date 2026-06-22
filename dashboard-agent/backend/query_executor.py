"""Execute validated SQL against the read-only database.

Everything runs as the SELECT-only role, inside a READ ONLY transaction, with a
per-statement timeout so a pathological query (cartesian join, full scan) can't
hang the service. Results are coerced to JSON-serializable Python so they can be
embedded directly in a WidgetSpec and shipped to the browser.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import config
from db import readonly_pool


@dataclass
class QueryResult:
    columns: list[tuple[str, str]]  # (name, dtype)
    rows: list[dict[str, Any]]


def _jsonable(value: Any) -> Any:
    """Convert DB types Pydantic/JSON can't handle natively."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def execute(sql: str) -> QueryResult:
    """Run `sql` read-only with a statement timeout; return typed rows.

    Assumes `sql` has already passed sql_guard.sanitize(). Raises whatever
    psycopg raises on a DB error; the agent layer maps that to QueryExecutionError.
    """
    with readonly_pool().connection() as conn:
        # Belt and suspenders: even though the role is read-only, mark the
        # transaction read-only and bound execution time.
        conn.execute("SET TRANSACTION READ ONLY")
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {config.STATEMENT_TIMEOUT_MS}")
            cur.execute(sql)
            description = cur.description or []
            colnames = [d.name for d in description]
            # psycopg exposes type OIDs; map a few common ones to friendly names
            # for the frontend's formatting hints.
            coltypes = [_oid_to_name(d.type_code) for d in description]
            raw_rows = cur.fetchall()

    rows = [
        {name: _jsonable(val) for name, val in zip(colnames, row)} for row in raw_rows
    ]
    return QueryResult(columns=list(zip(colnames, coltypes)), rows=rows)


# Minimal OID -> name map; unknown types fall back to "unknown". This is only a
# rendering hint, so it doesn't need to be exhaustive.
_OID_NAMES = {
    16: "bool",
    20: "int", 21: "int", 23: "int",
    700: "float", 701: "float", 1700: "numeric",
    25: "text", 1043: "text", 1042: "text",
    1082: "date", 1114: "timestamp", 1184: "timestamp",
}


def _oid_to_name(oid: int) -> str:
    return _OID_NAMES.get(oid, "unknown")
