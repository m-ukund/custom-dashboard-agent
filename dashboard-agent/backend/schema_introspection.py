"""Live schema introspection with a short TTL cache.

The agent can only generate safe, grounded SQL if it knows what tables and
columns actually exist *right now*. Because the assignment's data "may be
updating all the time" and the schema itself can drift, we re-read the catalog
from Postgres on a short TTL rather than baking the schema in at startup.

`schema_text()` returns a compact, prompt-friendly description that we feed to
the model at every stage (triage, SQL generation, spec generation).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import config
from db import owner_pool


@dataclass
class Column:
    name: str
    dtype: str
    nullable: bool


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)
    foreign_keys: list[str] = field(default_factory=list)  # human-readable "col -> table.col"


@dataclass
class Schema:
    tables: list[Table]
    captured_at: float

    def to_prompt_text(self) -> str:
        """Render the schema as compact text for an LLM prompt."""
        lines: list[str] = []
        for table in self.tables:
            cols = ", ".join(
                f"{c.name} {c.dtype}{'' if c.nullable else ' NOT NULL'}"
                for c in table.columns
            )
            lines.append(f"TABLE {table.name} ({cols})")
            for fk in table.foreign_keys:
                lines.append(f"  FK {fk}")
        return "\n".join(lines)

    def table_names(self) -> set[str]:
        return {t.name for t in self.tables}


_lock = threading.Lock()
_cached: Schema | None = None


_TABLES_SQL = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name
"""

_COLUMNS_SQL = """
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position
"""

_FK_SQL = """
SELECT
    tc.table_name      AS src_table,
    kcu.column_name    AS src_col,
    ccu.table_name     AS tgt_table,
    ccu.column_name    AS tgt_col
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
"""


def _read_schema() -> Schema:
    """Read the current public schema from the system catalogs (owner role)."""
    tables: dict[str, Table] = {}
    with owner_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_TABLES_SQL)
            for (name,) in cur.fetchall():
                tables[name] = Table(name=name)

            cur.execute(_COLUMNS_SQL)
            for table_name, col, dtype, nullable in cur.fetchall():
                if table_name in tables:
                    tables[table_name].columns.append(
                        Column(name=col, dtype=dtype, nullable=(nullable == "YES"))
                    )

            cur.execute(_FK_SQL)
            for src_table, src_col, tgt_table, tgt_col in cur.fetchall():
                if src_table in tables:
                    tables[src_table].foreign_keys.append(
                        f"{src_col} -> {tgt_table}.{tgt_col}"
                    )

    return Schema(tables=list(tables.values()), captured_at=time.monotonic())


def get_schema(force_refresh: bool = False) -> Schema:
    """Return a cached schema, refreshing if older than the TTL."""
    global _cached
    with _lock:
        fresh = (
            _cached is not None
            and not force_refresh
            and (time.monotonic() - _cached.captured_at) < config.SCHEMA_CACHE_TTL_S
        )
        if not fresh:
            _cached = _read_schema()
        return _cached


def schema_text(force_refresh: bool = False) -> str:
    return get_schema(force_refresh=force_refresh).to_prompt_text()
