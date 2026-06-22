"""Centralized, typed-ish configuration read from the environment.

Two distinct database identities matter here:

* OWNER_DSN     -- used only for schema introspection (reads system catalogs).
* READONLY_DSN  -- used to execute generated SQL. This role can only SELECT, so
                   it is the database-level backstop behind sql_guard.py.

Keeping them separate means a bug in the guard still can't write to the DB.
"""

from __future__ import annotations

import os

OWNER_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://dashboard_owner:owner_pw@localhost:5432/dashboard",
)

READONLY_DSN = os.environ.get(
    "READONLY_DATABASE_URL",
    "postgresql://dashboard_readonly:readonly_pw@localhost:5432/dashboard",
)

# Model configuration. Default to a model id that exists for this account; the
# takehome's lesson was to never hardcode a dead model id.
MODEL = os.environ.get("DASHBOARD_AGENT_MODEL", "claude-sonnet-4-6")
MAX_TOKENS = int(os.environ.get("DASHBOARD_AGENT_MAX_TOKENS", "1500"))

# Safety limits for query execution.
STATEMENT_TIMEOUT_MS = int(os.environ.get("DASHBOARD_STATEMENT_TIMEOUT_MS", "5000"))
MAX_ROWS = int(os.environ.get("DASHBOARD_MAX_ROWS", "1000"))

# How long an introspected schema snapshot is trusted before we re-read it.
# Short, because the assignment's data "may be updating all the time" and the
# schema itself can drift.
SCHEMA_CACHE_TTL_S = float(os.environ.get("DASHBOARD_SCHEMA_TTL_S", "30"))
