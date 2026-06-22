"""FastAPI entry point for the receipt parser.

Kept intentionally thin: it validates the request, delegates to
`receipt_parser.parse_receipt`, and maps the outcome to an HTTP response with a
clear status code and a structured body. All the reliability logic lives in
`receipt_parser.py` so it can be tested and evaluated without the HTTP layer.

Run with:  uvicorn scaffold:app --reload
"""

import logging
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from models import ErrorResponse, ParseResponse
from receipt_parser import ModelAPIError, ReceiptParseError, parse_receipt

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI(title="Receipt Parser")


class ReceiptRequest(BaseModel):
    receipt_text: str


def _error(status_code: int, error: str, detail: str, request_id: str) -> JSONResponse:
    body = ErrorResponse(error=error, detail=detail, request_id=request_id)
    return JSONResponse(status_code=status_code, content=body.model_dump())


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/parse")
def parse(request: ReceiptRequest):
    request_id = uuid.uuid4().hex[:12]
    try:
        result = parse_receipt(request.receipt_text, request_id=request_id)
    except ValueError as exc:
        return _error(400, "invalid_input", str(exc), request_id)
    except ModelAPIError as exc:
        return _error(502, "model_api_error", str(exc), exc.request_id)
    except ReceiptParseError as exc:
        return _error(422, "unparseable_output", str(exc), exc.request_id)

    response = ParseResponse(items=result.items)
    return JSONResponse(
        status_code=200,
        content={**response.model_dump(), "request_id": result.request_id},
    )
