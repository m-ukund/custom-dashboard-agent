# Submission Notes (written by Claude alone)

## The most important problem

The scaffold **trusted model output without validation**. It sent a vague prompt
("Parse this receipt and categorize each item: ...") and returned
`message.content[0].text` verbatim. There was no schema, no parsing, no
validation, and no error handling.

I confirmed this by actually running it. Two concrete failures:

1. **Unhandled API errors become 500s.** The hardcoded model id
  `claude-sonnet-4-20250514` is not available on this account, so a normal
   `POST /parse` returned a raw 500 with a stack trace
   (`anthropic.NotFoundError: 404`). Any API hiccup crashes the endpoint.
2. **The "happy path" output is unusable.** With a valid model, the raw response
  was a *Markdown table* with free-form categories like
   `Meals & Entertainment` and `Business/Technology Services` - none of which
   match the required set (`meals`, `travel`, `software`, `office_supplies`,
   `other`). The caller gets prose, not data.

So the fix had to make output **structured, validated, and untrusted until
proven valid**, and stop treating the model as infallible.

## What I built

- **Strict schema** ([models.py](models.py)): a `Category` enum and a `LineItem`
model (`item`, `amount`, `category`). Amounts that arrive as `"$1,204.99"`
strings are coerced and rounded; invalid categories are rejected.
- **A reliability pipeline** ([receipt_parser.py](receipt_parser.py), HTTP-free
so it is testable): schema-constrained prompt -> model call -> defensive text
extraction -> JSON extraction (strips ```json fences) -> Pydantic validation.
- **Explicit failure handling**: SDK errors are wrapped as `ModelAPIError`;
unparseable/invalid output becomes `ReceiptParseError`. The API
([scaffold.py](scaffold.py)) maps these to **400 / 502 / 422** with a
structured `{error, detail, request_id}` body instead of a 500.
- **One corrective retry**: on a parse/validation failure, the bad output and the
exact error are fed back asking for valid JSON only. If that also fails, a
structured error is returned.
- **Observability**: every attempt logs JSON with `request_id`, attempt count,
latency, input size, and the (truncated) raw response.
- **Configurable model**: env var `RECEIPT_PARSER_MODEL` with a working default,
so we are not bound to a dead model id.

## The heavy-hitter: an evaluation harness

You cannot improve reliability you do not measure. [evals/](evals/) contains a
labeled dataset (clean, messy, and adversarial - including a prompt-injection
attempt) and a runner that reports parse-success rate, item recall, and
category/amount accuracy, exiting non-zero below threshold so it can gate CI.

It runs in `--mock` mode (scripted responses, no API key, deterministic - good
for CI) and live mode. Running it live immediately caught a **wrong assumption of
mine**: I expected `"?????"` to be unparseable, but the model correctly returns
an empty item list, so I corrected the dataset. That is exactly the point of an
eval - it checks the system against reality, not against my guesses.

## What I deliberately left out

- **Tool-use / JSON-schema enforced output.** Prompt-and-parse + validation is
more transparent to demonstrate; tool-use is the natural next step for even
higher reliability.
- Auth, rate limiting, persistence, batching, async client. Single-call latency
is fine here and FastAPI runs the sync route in a threadpool.

## Where it would still break / next steps

- A model that confidently hallucinates a *well-formed but wrong* item passes
schema validation. The eval harness is the guardrail; I'd grow the dataset and
add field-level confidence/`needs_review` flags.
- The corrective retry is single-shot and not backed off; I'd add jittered
retries for transient API errors specifically.
- I'd move the API key / model config into typed settings and add request-level
timeouts.

## How I used AI tools

- Used the assistant to read and run the scaffold, reproduce the failures, and
scaffold the parser, eval harness, and tests.
- I verified rather than trusted: I ran the live API to see the real raw output
(Markdown, not JSON), discovered the hardcoded model 404s, and caught my own
bad dataset assumption via the live eval. The full prompt history is in
[PROMPT_LOG.md](PROMPT_LOG.md).

