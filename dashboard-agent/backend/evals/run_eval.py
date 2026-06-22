"""Evaluation harness for the dashboard agent.

Runs the agent over a labeled dataset and reports the metrics that matter for an
agentic system: did it behave as expected (produce a widget vs. fail correctly),
did it choose the right widget type, and did unsafe/invalid model output get
caught by the guard + validation (with corrective retries) rather than slipping
through. Exits non-zero below threshold so it can gate CI.

    python -m evals.run_eval --mock     # deterministic, no API key, no DB
    python -m evals.run_eval            # live: needs ANTHROPIC_API_KEY + DB

You cannot improve reliability you do not measure; this is how we measure it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent
from models import AgentError
from evals.mock_client import MockAnthropic, make_executor
from evals.mock_responses import MOCK_RESPONSES, SCHEMA_TEXT

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.jsonl")


@dataclass
class CaseScore:
    name: str
    type: str
    behaved_ok: bool          # produced a widget when expected, errored when expected
    widget_type_ok: bool
    note: str = ""


def _load_dataset() -> list[dict]:
    cases = []
    with open(DATASET_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def _run_case(case: dict, mock: bool) -> CaseScore:
    name, ctype = case["name"], case["type"]
    expect_error = case.get("expect_error", False)
    expected_type = case.get("expected_widget_type")
    expected_error = case.get("expected_error")

    if mock:
        spec = MOCK_RESPONSES.get(name, {"model": ["{}"], "result": None})
        client = MockAnthropic(list(spec["model"]))
        kwargs = dict(
            client=client,
            schema_provider=lambda: SCHEMA_TEXT,
            executor=make_executor(spec["result"]),
        )
    else:
        import anthropic
        kwargs = dict(client=anthropic.Anthropic())  # live: real schema + executor

    try:
        result = agent.run(case["request"], **kwargs)
    except AgentError as exc:
        if expect_error:
            ok = expected_error is None or exc.error_code == expected_error
            return CaseScore(name, ctype, ok, True,
                             note=f"failed as expected ({exc.error_code})")
        return CaseScore(name, ctype, False, False, note=f"unexpected error: {exc}")
    except ValueError as exc:
        if expect_error:
            return CaseScore(name, ctype, True, True, note=f"invalid input: {exc}")
        return CaseScore(name, ctype, False, False, note=f"value error: {exc}")

    if expect_error:
        return CaseScore(name, ctype, False, False, note="expected an error but succeeded")

    wtype = result.widget.type.value
    type_ok = expected_type is None or wtype == expected_type
    note = f"{wtype}, {result.attempts} attempt(s)"
    return CaseScore(name, ctype, True, type_ok, note=note)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dashboard agent eval harness")
    parser.add_argument("--mock", action="store_true", help="scripted, no API key / DB")
    parser.add_argument("--threshold", type=float, default=0.9, help="min pass rate (0-1)")
    args = parser.parse_args()

    cases = _load_dataset()
    scores = [_run_case(c, args.mock) for c in cases]

    print(f"\nDashboard agent evaluation ({'mock' if args.mock else 'live'})")
    print("=" * 76)
    print(f"{'case':<24}{'type':<13}{'behaved':<10}{'type':<7}note")
    print("-" * 76)
    for s in scores:
        behaved = "ok" if s.behaved_ok else "FAIL"
        typ = "ok" if s.widget_type_ok else "x"
        print(f"{s.name:<24}{s.type:<13}{behaved:<10}{typ:<7}{s.note}")

    total = len(scores)
    behaved = sum(1 for s in scores if s.behaved_ok)
    type_ok = sum(1 for s in scores if s.widget_type_ok)
    behave_rate = behaved / total if total else 0.0
    type_rate = type_ok / total if total else 0.0

    print("-" * 76)
    print(f"behaved-as-expected : {behave_rate:.0%}  ({behaved}/{total} cases)")
    print(f"widget-type accuracy: {type_rate:.0%}  ({type_ok}/{total} cases)")
    print("=" * 76)

    passed = behave_rate >= args.threshold
    print("RESULT:", "PASS" if passed else "FAIL", f"(threshold {args.threshold:.0%})\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
