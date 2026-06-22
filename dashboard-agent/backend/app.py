"""FastAPI entry point for the dashboard agent.

Kept deliberately thin (like the takehome's scaffold): validate the request,
delegate to `agent.run`, and map the outcome to an HTTP response with a clear
status code and a structured body. All reliability logic lives in `agent.py` so
it stays testable without the HTTP layer.

Run with:  uvicorn app:app --reload
"""

from __future__ import annotations

import logging
import uuid
from collections import deque

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import agent
import schema_introspection
from models import AgentError, ErrorResponse, WidgetRequest

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI(title="Custom Dashboard Agent")

# The React dev server runs on a different origin; allow it in this prototype.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep the last N traces in memory so failures are inspectable via /traces
# without needing a log aggregator in this prototype.
_RECENT_TRACES: deque = deque(maxlen=50)


def _error(status: int, error: str, detail: str, stage: str, request_id: str,
           clarification: str | None = None) -> JSONResponse:
    body = ErrorResponse(
        error=error, detail=detail, stage=stage,
        request_id=request_id, clarification=clarification,
    )
    return JSONResponse(status_code=status, content=body.model_dump())


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/schema")
def schema() -> dict:
    """Expose the current (live) schema so the UI can show what's queryable."""
    snapshot = schema_introspection.get_schema()
    return {
        "tables": [
            {
                "name": t.name,
                "columns": [{"name": c.name, "dtype": c.dtype} for c in t.columns],
                "foreign_keys": t.foreign_keys,
            }
            for t in snapshot.tables
        ]
    }


@app.get("/traces")
def traces() -> dict:
    """Most recent request traces, newest first (debugging aid)."""
    return {"traces": list(reversed(_RECENT_TRACES))}


@app.post("/widgets")
def create_widget(request: WidgetRequest):
    """Turn a natural-language request into a validated, renderable widget."""
    request_id = uuid.uuid4().hex[:12]
    try:
        result = agent.run(
            request.request,
            previous_widget=request.previous_widget,
            request_id=request_id,
        )
    except ValueError as exc:
        _RECENT_TRACES.append({"request_id": request_id, "error": str(exc)})
        return _error(400, "invalid_input", str(exc), "input", request_id)
    except AgentError as exc:
        _RECENT_TRACES.append({
            "request_id": exc.request_id, "stage": exc.stage, "error": str(exc),
        })
        clarification = getattr(exc, "clarification", None)
        return _error(
            exc.http_status, exc.error_code, str(exc), exc.stage,
            exc.request_id, clarification,
        )

    _RECENT_TRACES.append({"request_id": result.request_id, "trace": result.trace})
    return JSONResponse(
        status_code=200,
        content={
            "widget": result.widget.model_dump(),
            "request_id": result.request_id,
            "attempts": result.attempts,
            "latency_ms": round(result.latency_ms, 1),
        },
    )
