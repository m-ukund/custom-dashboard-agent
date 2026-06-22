"""Pydantic schema for the receipt parser.

The whole point of this module is to make model output *untrusted until proven
valid*. Everything the model returns is forced through these models before it
can reach a caller.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    """The only categories a line item is allowed to have."""

    meals = "meals"
    travel = "travel"
    software = "software"
    office_supplies = "office_supplies"
    other = "other"


class LineItem(BaseModel):
    """A single validated expense line item."""

    item: str = Field(..., min_length=1)
    amount: float = Field(..., ge=0)
    category: Category

    @field_validator("amount", mode="before")
    @classmethod
    def _coerce_amount(cls, value: object) -> object:
        """Accept "$1,234.50" style strings the model sometimes emits."""
        if isinstance(value, str):
            cleaned = value.strip().lstrip("$").replace(",", "").replace("$", "")
            return cleaned
        return value

    @field_validator("amount")
    @classmethod
    def _round_amount(cls, value: float) -> float:
        return round(float(value), 2)


class ParseResponse(BaseModel):
    """The validated, structured result returned to callers."""

    items: list[LineItem]


class ErrorResponse(BaseModel):
    """A structured error so callers learn *what* went wrong, not just a 500."""

    error: str
    detail: str
    request_id: str
