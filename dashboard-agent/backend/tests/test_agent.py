import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import agent
from models import (
    ModelAPIError,
    SQLValidationError,
    UnanswerableRequestError,
)
from evals.mock_client import MockAnthropic, make_executor
from evals.mock_responses import MOCK_RESPONSES, SCHEMA_TEXT


def _run(name: str, request: str = "test request"):
    spec = MOCK_RESPONSES[name]
    return agent.run(
        request,
        client=MockAnthropic(list(spec["model"])),
        schema_provider=lambda: SCHEMA_TEXT,
        executor=make_executor(spec["result"]),
    )


def test_happy_path_line_chart():
    result = _run("clean_revenue_region")
    assert result.widget.type.value == "line"
    assert result.attempts == 1
    assert result.widget.encoding.x == "week"
    assert len(result.widget.data) == 3


def test_metric_widget():
    result = _run("mau_metric")
    assert result.widget.type.value == "metric"
    assert result.widget.encoding.value == "active_users"


def test_unanswerable_raises_with_clarification():
    with pytest.raises(UnanswerableRequestError) as exc:
        _run("ambiguous_clarify")
    assert exc.value.clarification


def test_unsafe_sql_triggers_corrective_retry():
    # First plan stacks a DROP; guard rejects; the scripted retry is clean.
    result = _run("sql_guard_retry")
    assert result.attempts == 2
    assert "drop" not in result.widget.sql.lower()


def test_bad_spec_triggers_corrective_retry():
    result = _run("spec_retry")
    assert result.attempts == 2
    assert result.widget.type.value == "bar"
    assert result.widget.encoding.x == "category"


def test_model_api_error_is_wrapped():
    with pytest.raises(ModelAPIError):
        _run("model_api_error")


def test_empty_request_rejected():
    with pytest.raises(ValueError):
        agent.run("   ", client=MockAnthropic(["{}"]),
                  schema_provider=lambda: SCHEMA_TEXT, executor=make_executor(None))


def test_unsafe_sql_exhausts_retries():
    # Both attempts return unsafe SQL -> SQLValidationError after the retry.
    bad = MOCK_RESPONSES["sql_guard_retry"]["model"][1]
    triage = MOCK_RESPONSES["sql_guard_retry"]["model"][0]
    with pytest.raises(SQLValidationError):
        agent.run(
            "count orders",
            client=MockAnthropic([triage, bad, bad]),
            schema_provider=lambda: SCHEMA_TEXT,
            executor=make_executor(MOCK_RESPONSES["sql_guard_retry"]["result"]),
        )
