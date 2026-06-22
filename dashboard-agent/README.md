# Custom Dashboard Agent

Connect a PostgreSQL database, ask for charts and metrics in plain English, and
iteratively build a dashboard on top of your own data. The agent turns a
natural-language request into a **safe, read-only SQL query** and a
**validated, renderable widget**, treating every model output as untrusted until
it passes schema and safety checks.

```
NL request ─▶ web client ─▶ FastAPI ─▶ agent
   triage (answerable vs live schema?) ─▶ NL→SQL ─▶ SQL guard ─▶ read-only execute
   ─▶ build + validate WidgetSpec ─▶ JSON ─▶ React renders metric / line / bar / table
```

## Architecture

| Layer | Files | Responsibility |
|-------|-------|----------------|
| Database | `db/schema.sql`, `db/seed.py`, `db/roles.sql`, `docker-compose.yml` | Dockerized Postgres, generated e-commerce data, SELECT-only role |
| Schema | `backend/schema_introspection.py` | Live, TTL-cached schema read from the catalog |
| Agent core | `backend/agent.py` | Triage → SQL → guard → execute → spec, with corrective retries (HTTP-free) |
| Schema/contract | `backend/models.py` | `WidgetSpec` + typed errors; model output untrusted until validated |
| Safety | `backend/sql_guard.py`, `backend/query_executor.py` | Read-only single-SELECT enforcement, statement timeout, row cap |
| API | `backend/app.py` | Thin FastAPI; maps typed errors to 400/422/502 |
| Frontend | `frontend/` | React + Recharts; generic widget renderer, iterative edits |
| Reliability | `backend/evals/`, `backend/demo/`, `backend/tests/` | Eval harness (mock + live), demo artifacts, unit tests |

## Quickstart

### 1. Database

```bash
cd dashboard-agent
docker compose up -d            # starts Postgres, applies schema.sql + roles.sql
pip install -r backend/requirements.txt
python db/seed.py               # generate ~200 customers / 4000 orders / 12000 events
```

Optional — simulate the "data is always updating" property in another terminal:

```bash
python db/seed.py --simulate    # inserts a fresh order + event every couple seconds
```

### 2. Backend API

```bash
cd backend
export ANTHROPIC_API_KEY=sk-...          # Windows PowerShell: $env:ANTHROPIC_API_KEY="sk-..."
uvicorn app:app --reload                 # http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173 (proxies /api -> :8000)
```

Open http://localhost:5173 and try "Show weekly revenue by region", then refine a
widget with "break this down by product category".

## Reliability without the full stack

The agent core is dependency-injected, so the eval harness and tests run with
**no API key and no database** using scripted model responses:

```bash
cd backend
python -m evals.run_eval --mock          # deterministic; gates on behaved-as-expected rate
python -m pytest -q                      # unit tests: guard, schema validation, agent paths
```

Live end-to-end demo (needs DB + API key), writes input/output artifacts:

```bash
python demo/run_demo.py
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/widgets` | NL request → validated `WidgetSpec` (optionally edits a `previous_widget`) |
| GET | `/schema` | Current live schema (tables, columns, FKs) |
| GET | `/traces` | Last 50 request traces for debugging |
| GET | `/health` | Liveness |

## Failure handling

Errors are structured (`{error, detail, stage, request_id, clarification?}`), never
bare 500s:

- `400 invalid_input` — empty/garbage request
- `422 unanswerable_request` — triage can't map it to the schema (returns a clarifying question)
- `502 model_api_error` — Anthropic network/auth/rate-limit failure
- `422 sql_validation_error` — generated SQL stayed unsafe after a corrective retry
- `422 query_execution_error` — DB error / statement timeout
- `422 spec_validation_error` — widget spec couldn't be validated against the real columns

See [NOTES.md](NOTES.md) for scope, tradeoffs, and what would change to productionize.
