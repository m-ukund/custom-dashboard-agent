"""A minimal stand-in for `anthropic.Anthropic` for deterministic testing.

It returns a pre-scripted sequence of responses (one per `messages.create`
call), which lets us exercise the success path, the corrective-retry path, and
hard failures without touching the network or needing an API key.
"""

from __future__ import annotations


class _Block:
    def __init__(self, text: str):
        self.text = text


class _Message:
    def __init__(self, text: str):
        self.content = [_Block(text)]


class _EmptyMessage:
    content: list = []


class _Messages:
    def __init__(self, owner: "MockAnthropic"):
        self._owner = owner

    def create(self, **_kwargs):
        self._owner.calls += 1
        responses = self._owner.responses
        # Use the next scripted response; repeat the last one if we run out.
        index = min(self._owner.calls - 1, len(responses) - 1)
        item = responses[index]
        if isinstance(item, Exception):
            raise item
        if item is None:
            return _EmptyMessage()
        return _Message(item)


class MockAnthropic:
    """Drop-in replacement that yields scripted responses.

    `responses` is a list where each element is either a string (returned as the
    model's text), an Exception (raised), or None (an empty content response).
    """

    def __init__(self, responses: list):
        self.responses = responses or [""]
        self.calls = 0
        self.messages = _Messages(self)
