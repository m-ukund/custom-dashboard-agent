# Prompt History

A chronological record of the prompts I (the user) gave during this session,
plus the answers I selected for the multiple-choice questions the assistant
posed (during planning and during setup). Terminal snippets I referenced are
summarized in brackets.

---

## Phase 1 — Planning (Plan Mode)

### Prompt 1 — Study the assignment and produce a plan

> Could you please thoroughly study this assignment `Agentic AI Engineering Interview Problem.md`?
>
> Dive deep into the assignment. Think about system design principles and come up with a plan for this custom dashboard.
>
> For my plan, please study `Excalidraw Whiteboarding.svg` in depth. If the SVG is confusing, analyze the PNG: `ai-plan.png`. Take a look at my structure: we want to support PostgreSQL, we want Claude to make a local database filled with a bunch of generated data, we want a web client that we can access, and an API that serves the client, and that connected to a backend that has code that executes the user's query and code that visualizes the result.
>
> Some assumptions: The data is read only. The internal dashboard for the data may be updating all the time! It's not fixed, new data can end up coming in at any time. We want our data structured in JSON, and a component on the front-end that can render the structured data from the JSON.
>
> We want a standardized output schema, which can be somewhat dynamic depending on the prompts and the data involved.
>
> We also want a visually clear GUI for our web client front-end.
>
> We want our output to be structured and validated, and we want failure cases to be handled explicitly. Model API errors should be handled instead of letting them propagate as unhandled exceptions. We also want observability: any failures should be clearly logged and identified for us to diagnose later.
>
> Think about how prompts can be messy, and think about how agent results are not deterministic. Factor all of these issues into the final system.
>
> Also dive deep and analyze the git repo found in the folder `ai-systems-takehome-main`. This should give you an idea of how to structure a web client and the entire system!
>
> Please ask me if you have questions with the system design as you plan it out.

### Questions the assistant posed during planning (and my answers)

**Q1. How should the "standardized but dynamic" output schema + frontend rendering work?**
Options:
- (a) Custom JSON "widget spec" validated by Pydantic, rendered by a generic React component using Recharts *(Recommended)*
- (b) Adopt Vega-Lite specs as the standardized schema
- (c) Custom widget spec for metrics/tables + Vega-Lite for charts (hybrid)

**My answer: (a) Custom widget spec + Recharts.**

**Q2. What build scope should the plan target?**
Options:
- (a) Full vertical prototype: Dockerized PostgreSQL + FastAPI agent + React dashboard + eval harness + observability *(Recommended)*
- (b) Backend slice only (no React GUI)
- (c) Thin backend + polished React dashboard emphasis

**My answer: (a) Full vertical prototype.**

---

## Phase 2 — Build

### Prompt 2 — Implement the plan

> Custom Dashboard Agent
>
> Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.
>
> To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

*(The assistant then implemented all 9 todos: database, models, schema introspection, SQL guard + executor, agent pipeline, FastAPI app, React/Recharts frontend, eval harness + demo, and docs. 28 unit tests and the mock eval passed.)*

---

## Phase 3 — Running it / Troubleshooting

### Prompt 3 — First error + how to see the web app

> [Referenced terminal showing `The token '&&' is not a valid statement separator in this version`]
> Why is this error happening here? I want to be able to see the web app and submit a request. Could you tell me how?

**Question the assistant posed:** Given Docker/Node/API key weren't installed, how do you want to get to a usable web app?
Options:
- (a) Add a no-install offline demo (SQLite + mock agent + no-build React)
- (b) Offline DB + no-build frontend, but use the real Claude agent
- (c) I'll install the real stack myself (Docker + Node + API key) — just give exact PowerShell steps

**My answer: (c) Install the real stack myself.**

### Prompt 4 — Node PATH + Docker

> [Referenced terminal showing `node : The term 'node' is not recognized...`]
> How do we make sure that the node command is on my PATH? (I haven't yet started Docker Desktop. Should I?)

### Prompt 5 — Is Docker running?

> [Referenced terminal showing `docker --version` -> 29.5.3 and `docker ps` printing an empty table header]
> Is docker running?

### Prompt 6 — Explain the uvicorn error

> [Referenced terminal showing `ERROR: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`]
> Can you explain this error?

*(Cause: a stale `python3.12` process from 6/18 was already listening on port 8000.)*

### Prompt 7 — npm not recognized at Step 3

> [Referenced terminal showing `npm : The term 'npm' is not recognized...`]
> This error happens when I run Step 3 -- Web Client.

---

## Phase 4 — Publishing to GitHub

### Prompt 8 — Create repo and push

> Can you please make a new github repo and commit and push?

**Questions the assistant posed (and my answers):**

**Q1. What should the new repo contain?**
- (a) Only `dashboard-agent/` *(Recommended)*
- (b) The entire workspace
- (c) `dashboard-agent/` + assignment & whiteboard files (not the prior take-home)

**My answer: (b) The entire workspace.**

**Q2. Private or public?**
- (a) Private *(Recommended)*
- (b) Public

**My answer: (b) Public.**

**Q3. Repository name?**
- (a) `dashboard-agent` *(Recommended)*
- (b) `custom-dashboard-agent`

**My answer: (b) `custom-dashboard-agent`.**

*(Result: pushed to https://github.com/m-ukund/custom-dashboard-agent — public, 80 files, branch `main`.)*

---

## Phase 5 — This document

### Prompt 9 — Create prompt history

> Could you please create a document with my prompt history? Include any responses to questions that Claude posed in the plan.
