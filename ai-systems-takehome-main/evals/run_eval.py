"""Evaluation harness for the receipt parser.

Runs the parser over a labeled dataset and reports parse-success rate plus
field-level accuracy (item recall, category accuracy, amount accuracy). Exits
non-zero when below threshold so it can gate CI.

    python -m evals.run_eval --mock          # deterministic, no API key
    python -m evals.run_eval                 # live, needs ANTHROPIC_API_KEY

You cannot improve reliability you do not measure; this is how we measure it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

# Allow `python evals/run_eval.py` as well as `python -m evals.run_eval`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from receipt_parser import ModelAPIError, ParseResult, ReceiptParseError, parse_receipt
from evals.mock_client import MockAnthropic
from evals.mock_responses import MOCK_RESPONSES

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.jsonl")


@dataclass
class CaseScore:
    name: str
    type: str
    parsed_ok: bool
    expected_items: int
    matched_items: int
    correct_category: int
    correct_amount: int
    note: str = ""


def _normalize(name: str) -> str:
    return " ".join(name.lower().split())


def _score_items(expected: list[dict], predicted: list) -> tuple[int, int, int]:
    """Greedy match predicted items to expected by normalized name."""
    matched = correct_category = correct_amount = 0
    remaining = list(predicted)
    for exp in expected:
        exp_name = _normalize(exp["item"])
        hit = None
        for pred in remaining:
            pred_name = _normalize(pred.item)
            if exp_name == pred_name or exp_name in pred_name or pred_name in exp_name:
                hit = pred
                break
        if hit is None:
            continue
        remaining.remove(hit)
        matched += 1
        if hit.category.value == exp["category"]:
            correct_category += 1
        if abs(float(hit.amount) - float(exp["amount"])) < 0.01:
            correct_amount += 1
    return matched, correct_category, correct_amount


def _load_dataset() -> list[dict]:
    cases = []
    with open(DATASET_PATH, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def _run_case(case: dict, mock: bool, model: str | None) -> CaseScore:
    name = case["name"]
    expected = case.get("expected", [])
    expect_error = case.get("expect_error", False)

    if mock:
        client = MockAnthropic(MOCK_RESPONSES.get(name, ["{}"]))
    else:
        import anthropic

        client = anthropic.Anthropic()

    try:
        result: ParseResult = parse_receipt(
            case["receipt_text"], client=client, model=model
        )
    except (ReceiptParseError, ModelAPIError) as exc:
        if expect_error:
            return CaseScore(name, case["type"], True, 0, 0, 0, 0, note="failed as expected")
        return CaseScore(
            name, case["type"], False, len(expected), 0, 0, 0, note=f"error: {exc}"
        )

    if expect_error:
        return CaseScore(
            name, case["type"], False, 0, 0, 0, 0, note="expected an error but parsed"
        )

    matched, cat_ok, amt_ok = _score_items(expected, result.items)
    note = f"{result.attempts} attempt(s)"
    return CaseScore(
        name, case["type"], True, len(expected), matched, cat_ok, amt_ok, note
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Receipt parser eval harness")
    parser.add_argument(
        "--mock", action="store_true", help="use scripted responses (no API key)"
    )
    parser.add_argument("--model", default=None, help="override model id (live mode)")
    parser.add_argument(
        "--threshold", type=float, default=0.8, help="min pass rate (0-1)"
    )
    args = parser.parse_args()

    cases = _load_dataset()
    scores = [_run_case(c, args.mock, args.model) for c in cases]

    print(f"\nReceipt parser evaluation ({'mock' if args.mock else 'live'})")
    print("=" * 72)
    header = f"{'case':<26}{'type':<12}{'parsed':<8}{'items':<8}{'cat':<7}{'amt':<7}note"
    print(header)
    print("-" * 72)
    for s in scores:
        items = f"{s.matched_items}/{s.expected_items}" if s.expected_items else "-"
        cat = f"{s.correct_category}/{s.matched_items}" if s.matched_items else "-"
        amt = f"{s.correct_amount}/{s.matched_items}" if s.matched_items else "-"
        parsed = "ok" if s.parsed_ok else "FAIL"
        print(f"{s.name:<26}{s.type:<12}{parsed:<8}{items:<8}{cat:<7}{amt:<7}{s.note}")

    total = len(scores)
    parsed_ok = sum(1 for s in scores if s.parsed_ok)
    total_expected = sum(s.expected_items for s in scores)
    total_matched = sum(s.matched_items for s in scores)
    total_cat = sum(s.correct_category for s in scores)
    total_amt = sum(s.correct_amount for s in scores)

    parse_rate = parsed_ok / total if total else 0.0
    recall = total_matched / total_expected if total_expected else 1.0
    cat_acc = total_cat / total_matched if total_matched else 0.0
    amt_acc = total_amt / total_matched if total_matched else 0.0

    print("-" * 72)
    print(f"parse success rate : {parse_rate:.0%}  ({parsed_ok}/{total} cases)")
    print(f"item recall        : {recall:.0%}  ({total_matched}/{total_expected} items)")
    print(f"category accuracy  : {cat_acc:.0%}  ({total_cat}/{total_matched} matched)")
    print(f"amount accuracy    : {amt_acc:.0%}  ({total_amt}/{total_matched} matched)")
    print("=" * 72)

    passed = parse_rate >= args.threshold and cat_acc >= args.threshold
    print("RESULT:", "PASS" if passed else "FAIL", f"(threshold {args.threshold:.0%})\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
