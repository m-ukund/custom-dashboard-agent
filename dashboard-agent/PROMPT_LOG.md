# Prompt Log

How AI tooling was used to build this system, and how its output was checked
rather than blindly trusted.

## Planning

- Studied the assignment, my whiteboard (`Excalidraw Whiteboarding.svg` /
  `ai-plan.png`), and the prior receipt-parser takehome to extract a reusable
  reliability blueprint (untrusted model output, typed errors, corrective retry,
  structured logging, eval harness).
- Decided two questions actually changed the design and asked them explicitly:
  the output-schema/charting approach (chose a custom `WidgetSpec` + Recharts),
  and the build scope (chose the full vertical prototype).

## Building

- Generated the e-commerce schema and seed data to support every example request
  ("weekly revenue by region", "top customers", "monthly active users",
  "by category"). Added a `--simulate` mode to model the "data is always
  updating" requirement.
- Built the agent as a dependency-injected, HTTP-free core so it could be tested
  and evaluated without a DB or API key — the same pattern that made the takehome
  testable.
- Designed the failure taxonomy first (triage / SQL guard / execution / spec) and
  mapped each to an HTTP status, then implemented the single-corrective-retry loop
  around it.

## Verifying (not trusting)

- Wrote `pytest` cases that prove the guard rejects stacked statements, DML, and
  system-catalog probes while allowing columns named like keywords (`status`,
  `updated_at`) — exactly the kind of false-positive an LLM-written regex guard
  tends to introduce. Caught and fixed the word-boundary handling there.
- Built a mock-backed eval harness covering the happy path, messy input,
  ambiguity, both corrective-retry paths (unsafe SQL, bad spec), and a simulated
  API error. Ran it: 100% behaved-as-expected, and the structured logs confirmed
  the retry paths actually fired rather than being dead code.
- Kept the model client mockable so reliability is measured deterministically in
  CI, with a separate live mode for end-to-end validation.

## What I'd ask the model to help with next

- Tool-use / JSON-schema-constrained generation to raise first-pass SQL validity.
- A larger, labeled eval set with semantic checks (not just "did it parse").
