"""Unit tests for the parsing/validation/retry logic.

These use the scripted MockAnthropic client so they run with no API key and no
network, and they cover the paths that actually matter for reliability: clean
success, format noise we recover from, invalid categories, the corrective
retry, hard failures, and API errors.
"""

import anthropic
import pytest

from evals.mock_client import MockAnthropic
from models import Category
from receipt_parser import ModelAPIError, ReceiptParseError, parse_receipt

GOOD = (
    '{"items": [{"item": "Uber Eats", "amount": 34.20, "category": "meals"},'
    ' {"item": "AWS invoice", "amount": 412.00, "category": "software"}]}'
)
RECEIPT = "Uber Eats $34.20\nAWS invoice $412.00"


def test_clean_json_parses_and_validates():
    result = parse_receipt(RECEIPT, client=MockAnthropic([GOOD]))
    assert len(result.items) == 2
    assert result.items[0].item == "Uber Eats"
    assert result.items[0].amount == 34.20
    assert result.items[1].category is Category.software
    assert result.attempts == 1


def test_code_fence_and_currency_strings_are_normalized():
    raw = (
        '```json\n{"items": [{"item": "Marriott", "amount": "$1,204.99",'
        ' "category": "travel"}]}\n```'
    )
    result = parse_receipt(RECEIPT, client=MockAnthropic([raw]))
    assert result.items[0].amount == 1204.99


def test_invalid_category_triggers_retry_then_succeeds():
    bad = '{"items": [{"item": "Lunch", "amount": 10, "category": "food"}]}'
    good = '{"items": [{"item": "Lunch", "amount": 10, "category": "meals"}]}'
    result = parse_receipt(RECEIPT, client=MockAnthropic([bad, good]))
    assert result.attempts == 2
    assert result.items[0].category is Category.meals


def test_prose_then_valid_json_recovers_on_retry():
    client = MockAnthropic(["Here you go!", GOOD])
    result = parse_receipt(RECEIPT, client=client)
    assert result.attempts == 2
    assert len(result.items) == 2


def test_unparseable_after_retry_raises():
    client = MockAnthropic(["nope", "still nope"])
    with pytest.raises(ReceiptParseError) as exc:
        parse_receipt(RECEIPT, client=client)
    assert exc.value.raw_response is not None
    assert exc.value.request_id


def test_empty_input_raises_value_error():
    with pytest.raises(ValueError):
        parse_receipt("   ", client=MockAnthropic([GOOD]))


def test_api_error_is_wrapped():
    err = anthropic.APIConnectionError(request=None)
    client = MockAnthropic([err])
    with pytest.raises(ModelAPIError) as exc:
        parse_receipt(RECEIPT, client=client)
    assert exc.value.request_id


def test_empty_content_block_raises_parse_error():
    with pytest.raises(ReceiptParseError):
        parse_receipt(RECEIPT, client=MockAnthropic([None, None]))
