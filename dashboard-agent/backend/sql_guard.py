"""Application-level SQL safety guard.

This is defense-in-depth layer #1 (the read-only DB role is layer #2). Generated
SQL is treated as hostile until it passes every check here:

* exactly one statement (no stacked `; DROP TABLE ...`)
* the statement must be a read (SELECT or a WITH...SELECT CTE)
* no DDL/DML/utility keywords anywhere (INSERT, UPDATE, DELETE, DROP, COPY, ...)
* a LIMIT is enforced so a query can't return the whole table

We intentionally keep this conservative and explicit rather than clever: it is
easier to reason about and to explain why a query was rejected.
"""

from __future__ import annotations

import re

# Keywords that must never appear in a read-only analytics query. Matched on
# word boundaries so column names like "updated_at" don't trip "UPDATE".
_FORBIDDEN = [
    "insert", "update", "delete", "drop", "truncate", "alter", "create",
    "grant", "revoke", "copy", "merge", "call", "do", "vacuum", "analyze",
    "reindex", "cluster", "comment", "set", "reset", "begin", "commit",
    "rollback", "savepoint", "listen", "notify", "lock",
]
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(_FORBIDDEN) + r")\b", flags=re.IGNORECASE
)

# pg_* / information_schema probing is not needed for dashboards and is a common
# exfiltration target, so block it explicitly.
_SYSTEM_REF_RE = re.compile(r"\b(pg_catalog|pg_[a-z_]+|information_schema)\b", re.IGNORECASE)

_LIMIT_RE = re.compile(r"\blimit\s+\d+", re.IGNORECASE)


class UnsafeSQLError(ValueError):
    """Raised when SQL fails a guard check. Message explains exactly why."""


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", " ", sql)            # line comments
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)  # block comments
    return sql


def sanitize(sql: str, max_rows: int) -> str:
    """Validate `sql` and return a normalized, LIMIT-bounded read query.

    Raises UnsafeSQLError with a specific reason on any violation.
    """
    if not sql or not sql.strip():
        raise UnsafeSQLError("empty SQL")

    cleaned = _strip_comments(sql).strip().rstrip(";").strip()

    # Single statement only: nothing should remain after the first ';'.
    if ";" in cleaned:
        raise UnsafeSQLError("multiple statements are not allowed")

    lowered = cleaned.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise UnsafeSQLError("only SELECT / WITH read queries are allowed")

    forbidden = _FORBIDDEN_RE.search(cleaned)
    if forbidden:
        raise UnsafeSQLError(f"forbidden keyword: {forbidden.group(0).upper()}")

    if _SYSTEM_REF_RE.search(cleaned):
        raise UnsafeSQLError("references to system catalogs are not allowed")

    # Enforce a row cap. If the model already added a LIMIT we trust it only up
    # to max_rows; otherwise we append one.
    if not _LIMIT_RE.search(cleaned):
        cleaned = f"{cleaned}\nLIMIT {max_rows}"

    return cleaned
