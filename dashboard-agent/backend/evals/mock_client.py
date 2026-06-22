"""Deterministic stand-ins for the model client and the SQL executor.

These let the eval harness exercise the full agent pipeline -- triage, plan,
guard, execute, spec validation, and the corrective-retry path -- without an API
key or a running database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class _Block:
    def __init__(self, text: str):
        self.text = text


class _Message:
    def __init__(self, text: str):
        self.content = [_Block(text)]


class _Messages:
    def __init__(self, owner: "MockAnthropic"):
        self._owner = owner

    def create(self, **_kwargs):
        owner = self._owner
        index = min(owner.calls, len(owner.responses) - 1)
        owner.calls += 1
        item = owner.responses[index]
        if isinstance(item, Exception):
            raise item
        return _Message(item)


class MockAnthropic:
    """Yields a scripted sequence of responses, one per `messages.create` call.

    Each element is either a string (returned as model text) or an Exception
    (raised, to simulate an API failure).
    """

    def __init__(self, responses: list):
        self.responses = responses or ["{}"]
        self.calls = 0
        self.messages = _Messages(self)


@dataclass
class MockResult:
    """Mimics query_executor.QueryResult for the agent's duck-typed access."""

    columns: list[tuple[str, str]]
    rows: list[dict[str, Any]] = field(default_factory=list)


def make_executor(result: MockResult | None):
    """Return an executor callable that yields a canned result for any SQL."""
    def _execute(_sql: str) -> MockResult:
        if result is None:
            raise RuntimeError("no rows / table not found")
        return result
    return _execute
