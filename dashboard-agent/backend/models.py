"""Pydantic schemas + typed errors for the dashboard agent.

The guiding principle (carried over from the receipt-parser takehome) is that
*model output is untrusted until it passes through these schemas*. The agent
produces SQL and widget specs by prompting Claude; nothing the model emits
reaches the database or the browser until it has been validated here.

`WidgetSpec` is the standardized-but-dynamic contract between the agent and the
GUI: the same envelope describes a single metric, a line/bar chart, or a table.
Which `encoding` fields matter depends on `type`, which is what makes the schema
"dynamic" without becoming a free-for-all.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class WidgetType(str, Enum):
    """The only widget kinds the frontend knows how to render."""

    metric = "metric"
    line = "line"
    bar = "bar"
    table = "table"


class ColumnMeta(BaseModel):
    """One column of the executed result set."""

    name: str = Field(..., min_length=1)
    dtype: str = Field(default="unknown")


class Encoding(BaseModel):
    """How result columns map onto the chosen widget.

    Charts use x/y (+ optional series); metrics use `value` (+ optional
    `label`). Unused fields are simply left null. `value_format` is a hint the
    frontend uses to render numbers (e.g. "currency", "percent", "number").
    """

    x: str | None = None
    y: str | None = None
    series: str | None = None
    value: str | None = None
    label: str | None = None
    value_format: str | None = None


class WidgetSpec(BaseModel):
    """A validated, renderable dashboard widget plus its backing data."""

    id: str
    title: str = Field(..., min_length=1)
    request: str = Field(..., min_length=1)
    type: WidgetType
    sql: str = Field(..., min_length=1)
    columns: list[ColumnMeta] = Field(default_factory=list)
    data: list[dict[str, Any]] = Field(default_factory=list)
    encoding: Encoding = Field(default_factory=Encoding)
    notes: str | None = None

    @model_validator(mode="after")
    def _check_encoding_matches_type(self) -> "WidgetSpec":
        """Reject specs whose encoding can't actually drive the widget type.

        This is the gate that turns a plausible-looking model response into a
        trustworthy one: a "line" chart with no x/y axis is not renderable, so
        we treat it as a validation failure and trigger a corrective retry
        rather than shipping a broken widget to the browser.
        """
        column_names = {c.name for c in self.columns}

        if self.type in (WidgetType.line, WidgetType.bar):
            if not self.encoding.x or not self.encoding.y:
                raise ValueError(f"{self.type.value} chart requires encoding.x and encoding.y")
            for axis in ("x", "y", "series"):
                col = getattr(self.encoding, axis)
                if col and column_names and col not in column_names:
                    raise ValueError(
                        f"encoding.{axis} '{col}' is not one of the result columns "
                        f"{sorted(column_names)}"
                    )
        elif self.type is WidgetType.metric:
            if not self.encoding.value:
                raise ValueError("metric widget requires encoding.value")
            if column_names and self.encoding.value not in column_names:
                raise ValueError(
                    f"encoding.value '{self.encoding.value}' is not one of the "
                    f"result columns {sorted(column_names)}"
                )
        # table: any columns are fine.
        return self


# ---- What the model is asked to return at each stage (pre-execution) --------


class TriageResult(BaseModel):
    """The model's judgment on whether a request is answerable from the schema."""

    answerable: bool
    reason: str = ""
    clarification: str | None = None


class SqlPlan(BaseModel):
    """The model's proposed query + how it intends to visualize the result."""

    sql: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    widget_type: WidgetType
    encoding: Encoding = Field(default_factory=Encoding)
    notes: str | None = None


# ---- API envelopes ----------------------------------------------------------


class WidgetRequest(BaseModel):
    """Incoming natural-language request, optionally editing an existing widget."""

    request: str
    previous_widget: WidgetSpec | None = None


class ErrorResponse(BaseModel):
    """Structured error so callers learn *what* failed, not just a 500.

    `stage` and `request_id` make a failure traceable straight to its log line.
    `clarification` is populated when the right move is to ask the user for more
    detail rather than report a hard failure.
    """

    error: str
    detail: str
    stage: str
    request_id: str
    clarification: str | None = None


# ---- Typed exceptions raised by the HTTP-free core --------------------------


class AgentError(Exception):
    """Base for everything the agent raises, carrying observability context."""

    error_code = "agent_error"
    http_status = 500

    def __init__(self, message: str, request_id: str, stage: str):
        super().__init__(message)
        self.request_id = request_id
        self.stage = stage


class UnanswerableRequestError(AgentError):
    """Triage decided the request can't be answered from the current schema."""

    error_code = "unanswerable_request"
    http_status = 422

    def __init__(self, message: str, request_id: str, clarification: str | None = None):
        super().__init__(message, request_id, stage="triage")
        self.clarification = clarification


class ModelAPIError(AgentError):
    """The model API call itself failed (network, auth, rate limit, bad model)."""

    error_code = "model_api_error"
    http_status = 502

    def __init__(self, message: str, request_id: str, stage: str = "model_call"):
        super().__init__(message, request_id, stage)


class SQLValidationError(AgentError):
    """Generated SQL was unsafe or malformed even after a corrective retry."""

    error_code = "sql_validation_error"
    http_status = 422

    def __init__(self, message: str, request_id: str, raw_sql: str | None = None):
        super().__init__(message, request_id, stage="sql_validation")
        self.raw_sql = raw_sql


class QueryExecutionError(AgentError):
    """The (validated) SQL failed at execution time -- timeout, DB error, etc."""

    error_code = "query_execution_error"
    http_status = 422

    def __init__(self, message: str, request_id: str):
        super().__init__(message, request_id, stage="query_execution")


class SpecValidationError(AgentError):
    """The widget spec couldn't be validated even after a corrective retry."""

    error_code = "spec_validation_error"
    http_status = 422

    def __init__(self, message: str, request_id: str, raw_response: str | None = None):
        super().__init__(message, request_id, stage="spec_validation")
        self.raw_response = raw_response
