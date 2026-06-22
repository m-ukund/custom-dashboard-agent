"""Scripted model responses for `--mock` eval runs, keyed by dataset case name.

Each value is a list passed to MockAnthropic: one entry per `create` call. This
lets us deterministically exercise the full reliability loop without an API key:
clean successes, format noise we recover from, a successful corrective retry,
and a case that fails both attempts and must yield a structured error.
"""

MOCK_RESPONSES: dict[str, list] = {
    # Clean: perfect JSON on the first try.
    "clean_basic": [
        '{"items": [{"item": "Uber Eats", "amount": 34.20, "category": "meals"},'
        ' {"item": "AWS invoice", "amount": 412.00, "category": "software"},'
        ' {"item": "Office Depot", "amount": 28.50, "category": "office_supplies"},'
        ' {"item": "Delta Airlines", "amount": 890.00, "category": "travel"}]}'
    ],
    # Messy: model wraps JSON in a code fence and uses string amounts with "$"
    # and commas. The extractor strips the fence; the validator coerces amounts.
    "messy_currency": [
        '```json\n{"items": [{"item": "Marriott Hotel", "amount": "$1,204.99", "category": "travel"},'
        ' {"item": "GitHub Team Plan", "amount": "$44.00", "category": "software"},'
        ' {"item": "Lunch w/ client", "amount": "$87.50", "category": "meals"}]}\n```'
    ],
    "messy_multiline": [
        '{"items": [{"item": "Staples", "amount": 19.99, "category": "office_supplies"},'
        ' {"item": "Zoom subscription", "amount": 14.99, "category": "software"}]}'
    ],
    # Adversarial injection: a good model ignores the embedded instruction.
    "adversarial_injection": [
        '{"items": [{"item": "Lyft ride", "amount": 22.10, "category": "travel"},'
        ' {"item": "Notion annual", "amount": 96.00, "category": "software"}]}'
    ],
    # Prose: first attempt returns chatty prose (unparseable); the corrective
    # retry returns valid JSON. Demonstrates the retry actually recovering.
    "adversarial_prose_retry": [
        "Sure! It looks like you spent about $30 at Chipotle and $99 on Figma.",
        '{"items": [{"item": "Chipotle", "amount": 30.00, "category": "meals"},'
        ' {"item": "Figma seat", "amount": 99.00, "category": "software"}]}',
    ],
    # Meaningless input: a robust model returns an empty item list, which is
    # valid. (The hard-failure / retry-exhaustion path is covered by unit tests.)
    "adversarial_gibberish": ['{"items": []}'],
}
