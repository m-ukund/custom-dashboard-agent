# Submission Notes, written by Mukund Ramakrishnan

FOR THE USER:

Download this repository. Navigate to the "demo" folder. Take a look at run_demo.py. Put in some examples of your choosing. Then, run python run_demo.py, and watch the magic happen!

You will be asked for an ANTHROPIC_API_KEY which you should supply.


## What did Claude build for me?

- **models.py** — makes sure that model output is untrusted until proven valid. What the model returns is pushed through these models, ensuring that items are categorized accurately.
- **receipt_parser.py** — treats the model as unreliable, so the model's output is parsed, and if it doesn't fit our criteria exactly, it is fed back into the model ONE more time.
- **scaffold.py** — configures the FastAPI app. It's the entry point for the receipt parser (where you can put in your receipt). It creates an HTTP webpage through FastAPI. The main improvement that I made (with Claude's help) is CLASSIFYING possible errors to make the system more reliable. There are three possible errors:
  - `ValueError` → **400** (e.g. empty `receipt_text`) — the caller's fault.
  - `ModelAPIError` → **502** (the upstream model API failed — network, auth, rate limit, or the dead model id) — an upstream failure.
  - `ReceiptParseError` → **422** (the model responded but its output couldn't be validated even after the retry) — unprocessable.
- A table Claude made on what changed between the previous scaffold.py and this scaffold.py:


| **Aspect**     | **Original**                                                                     | **Now**                                                                |
| -------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Model call     | Made inline in the endpoint                                                      | Moved to `receipt_parser.py`; endpoint just delegates                  |
| Output         | Raw `message.content[0].text` (unstructured prose) returned as `{"result": ...}` | Validated `ParseResponse.items` (typed line items)                     |
| Error handling | None — any failure became an unhandled 500                                       | `try/except` mapping to 400 / 502 / 422 with structured bodies         |
| Traceability   | None                                                                             | `request_id` generated per call and returned/logged                    |
| Validation     | None                                                                             | Done upstream via Pydantic in `receipt_parser.py`                      |
| Retry          | None                                                                             | Single corrective retry (in `receipt_parser.py`)                       |
| Model id       | Hardcoded `claude-sonnet-4-20250514` (which 404s)                                | Configurable via `RECEIPT_PARSER_MODEL` env var in `receipt_parser.py` |
| Endpoints      | `/parse` only                                                                    | Added `/health`                                                        |


- Also, note that every attempt logs a JSON with `request_id`, attempt count, latency, input size, and a truncated raw response, for observability.

## Building Process

1. I tried to run the scaffold as-is. We know that in the beginning, the scaffold TRUSTED MODEL OUTPUT WITHOUT VALIDATION — the key problem we needed to fix — and sent a vague prompt and basically just "expected" it to work.
  1. What ended up happening was that unhandled API errors returned a 500. So any error with the API would crash the endpoint.
  2. When we did have a valid model, its output ended up being unusable. We got a markdown table with free-form categories that did not correspond to the fixed categories that we wanted (`meals`, `travel`, `software`, `office_supplies`, `other`).
2. Claude built models.py, receipt_parser.py, and scaffold.py. Later on, I had it build a run_demo.py that would neatly run the entire test harness and deposit inputs and outputs into a demo folder.

So, with the help of Claude, we have completed the FOUR SUGGESTED IMPROVEMENTS:

1. Making the output structured and validated
2. Handling failure cases explicitly
3. Adding a retry
4. Adding observability

To go above and beyond, we also built an EVALUATION HARNESS with a labeled dataset (clean, messy, and adversarial — including a prompt-injection attempt), and a way to run this evaluation harness. (We see in the live run a 100% success rate.)

With the help of AI, we have built a much stronger system than what we started with!

Take a look at run_results.png.


One additional thing that I left out that could be fixed: when we do an injection adversarial attack, the injection is treated as a unit of data, with price 0. It "passes" since the injection doesn't affect the computation; it's just being treated as data (our model is resisting). But, if we wanted stricter behavior and NO EXTRA ITEMS, the fix would be a small prompt tweak (e.g., "ignore lines that are not clearly an item with a price; do not invent amounts — never emit amount: 0") and/or a post-validation filter dropping amount == 0 items.

---

## The rest of these notes are written by Claude, and are here for reference

### The most important problem

The scaffold **trusted model output without validation**. It sent a vague prompt ("Parse this receipt and categorize each item: ...") and returned `message.content[0].text` verbatim. There was no schema, no parsing, no validation, and no error handling.

I confirmed this by actually running it. Two concrete failures:

1. **Unhandled API errors become 500s.** The hardcoded model id `claude-sonnet-4-20250514` is not available on this account, so a normal `POST /parse` returned a raw 500 with a stack trace (`anthropic.NotFoundError: 404`). Any API hiccup crashes the endpoint.
2. **The "happy path" output is unusable.** With a valid model, the raw response was a *Markdown table* with free-form categories like `Meals & Entertainment` and `Business/Technology Services` — none of which match the required set (`meals`, `travel`, `software`, `office_supplies`, `other`). The caller gets prose, not data.

So the fix had to make output **structured, validated, and untrusted until proven valid**, and stop treating the model as infallible.

### What I built

- **Strict schema** ([models.py](models.py)): a `Category` enum and a `LineItem` model (`item`, `amount`, `category`). Amounts that arrive as `"$1,204.99"` strings are coerced and rounded; invalid categories are rejected.
- **A reliability pipeline** ([receipt_parser.py](receipt_parser.py), HTTP-free so it is testable): schema-constrained prompt → model call → defensive text extraction → JSON extraction (strips ```json fences) → Pydantic validation.
- **Explicit failure handling**: SDK errors are wrapped as `ModelAPIError`; unparseable/invalid output becomes `ReceiptParseError`. The API ([scaffold.py](scaffold.py)) maps these to **400 / 502 / 422** with a structured `{error, detail, request_id}` body instead of a 500.
- **One corrective retry**: on a parse/validation failure, the bad output and the exact error are fed back asking for valid JSON only. If that also fails, a structured error is returned.
- **Observability**: every attempt logs JSON with `request_id`, attempt count, latency, input size, and the (truncated) raw response.
- **Configurable model**: env var `RECEIPT_PARSER_MODEL` with a working default, so we are not bound to a dead model id.

### The heavy-hitter: an evaluation harness

You cannot improve reliability you do not measure. `evals/` contains a labeled dataset (clean, messy, and adversarial — including a prompt-injection attempt) and a runner that reports parse-success rate, item recall, and category/amount accuracy, exiting non-zero below threshold so it can gate CI.

It runs in `--mock` mode (scripted responses, no API key, deterministic — good for CI) and live mode. Running it live immediately caught a **wrong assumption of mine**: I expected `"?????"` to be unparseable, but the model correctly returns an empty item list, so I corrected the dataset. That is exactly the point of an eval — it checks the system against reality, not against my guesses.

### What I deliberately left out

- **Tool-use / JSON-schema enforced output.** Prompt-and-parse + validation is more transparent to demonstrate; tool-use is the natural next step for even higher reliability.
- Auth, rate limiting, persistence, batching, async client. Single-call latency is fine here and FastAPI runs the sync route in a threadpool.

### Where it would still break / next steps

- A model that confidently hallucinates a *well-formed but wrong* item passes schema validation. The eval harness is the guardrail; I'd grow the dataset and add field-level confidence/`needs_review` flags.
- The corrective retry is single-shot and not backed off; I'd add jittered retries for transient API errors specifically.
- I'd move the API key / model config into typed settings and add request-level timeouts.

### How I used AI tools

- Used the assistant to read and run the scaffold, reproduce the failures, and scaffold the parser, eval harness, and tests.
- I verified rather than trusted: I ran the live API to see the real raw output (Markdown, not JSON), discovered the hardcoded model 404s, and caught my own bad dataset assumption via the live eval. The full prompt history is in [PROMPT_LOG.md](PROMPT_LOG.md).

