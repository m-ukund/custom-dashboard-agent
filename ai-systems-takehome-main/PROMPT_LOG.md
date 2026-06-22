# Prompt Log

## 1. Study the repo and plan

> Could you please thoroughly study this repository, and identify the most
> important problems? Could you build a plan on how to fix them, including making
> the meaningful improvements in README.md? And, in addition, could you also come
> up with one more heavy-hitting improvement that will make this submission
> shine? For now, please just thoroughly plan and explain what we should do.

Claude read every file and produced a plan: fix the core  
"model output trusted without validation" problem, add the README-listed  
improvements (structured output, error handling, retry, observability), and  
proposed an **evaluation harness** as the heavy-hitter. I picked the eval harness, which is what Claude built. 

## 2. Run the scaffold before changing anything

> Could we try running the scaffold as it is first?

Findings and issues:

- Only `pydantic` was installed; `fastapi`/`uvicorn`/`anthropic` were missing.
- With a valid Claude API key, `POST /parse` returned a **raw 500**:
`anthropic.NotFoundError: 404 - model: claude-sonnet-4-20250514` (the hardcoded
model id does not exist for this account).
- Reproducing with a valid model returned a **Markdown table** with free-form
categories - confirming the unstructured/unvalidated output problem.
- This also corrected an earlier assumption: the missing key does *not* crash at
import time in anthropic 0.105.2; it fails at request time.

## 3. Execute the plan

> Yes, execute the plan.

The assistant implemented `models.py`, `receipt_parser.py`, a thin `scaffold.py`,
the `evals/` harness, and `tests/`.

At a certain point, my API key was asked for, and I provided it. 

## 4. Extra clarifying questions (asked one-by-one):

> a. Where are the runs and the results?
>
> b. what terminal command should i run to see the results?
>
> c. Could you explain what [scaffold.py](http://scaffold.py)  is doing and the changes that were made?

These questions helped me clarify that (a) the runs took place in terminal and the results were printed to stdout. 

So this means that I could ask question (b), and then I got a list of commands, one of which would allow me to test the evaluation harness LIVE with the actual claude model, with a claude API key that I supplied. With this, I found that the evaluation scaffold was passing ALL tests, including with adversarial responses (injection, prose, and gibberish). 

The final question (c) helped me understand the HTTP entry point for the receipt parser, and how this would function "online" with FastAPI. The answer to this question helped me write the notes, and the table comes directly from the answer to this question. 

## 5. Final command (run demo and put neatly in folder):

>  Can you run the system and have the input and output clearly deposited in a demo folder?

This performed perfectly as expected. It used my claude API key to do a live run, and made a file run_demo.py to produce artifacts that are neatly placed in the folder demo.  We can see our outcome is as expected! 

## 6. Set prompt for API key:

>  Can you make it such that when I run run_[demo.py](http://demo.py), I'm asked for the key in the terminal?

This makes it such that I'm asked for the ANTHROPIC_API_KEY if one is not already set in the environment. I did not hard-code my own key, for security reasons!!! 

## Model used

`claude-sonnet-4-6` , through Cursor