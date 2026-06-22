"""Thin database access helpers.

Connection pools for the two identities (owner for introspection, read-only for
query execution). Pools are created lazily so that importing this module never
requires a live database -- important for unit tests and the mock-backed eval
harness, which never touch Postgres.
"""

from __future__ import annotations

from psycopg_pool import ConnectionPool

import config

_owner_pool: ConnectionPool | None = None
_readonly_pool: ConnectionPool | None = None


def owner_pool() -> ConnectionPool:
    """Pool for the owner role; used only to read system catalogs."""
    global _owner_pool
    if _owner_pool is None:
        _owner_pool = ConnectionPool(config.OWNER_DSN, min_size=1, max_size=4, open=True)
    return _owner_pool


def readonly_pool() -> ConnectionPool:
    """Pool for the SELECT-only role; used to run generated SQL."""
    global _readonly_pool
    if _readonly_pool is None:
        _readonly_pool = ConnectionPool(
            config.READONLY_DSN, min_size=1, max_size=8, open=True
        )
    return _readonly_pool


def close_pools() -> None:
    global _owner_pool, _readonly_pool
    if _owner_pool is not None:
        _owner_pool.close()
        _owner_pool = None
    if _readonly_pool is not None:
        _readonly_pool.close()
        _readonly_pool = None
