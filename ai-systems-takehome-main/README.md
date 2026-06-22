# AI Systems Take-Home: Receipt Parser

## Overview

This is a short, self-contained take-home assignment. We expect it to take between **60 and 75 minutes**. You should not spend more than 90 minutes on it.

You will be given a small Python web application that is partially broken. Your job is to read the code, identify the most important problem, and fix it.

We are not looking for a complete or production-ready solution. We are looking at how you read unfamiliar code, how you think about reliability, and how you approach building with AI tools.

> **A note on AI tools**
>
> You are encouraged to use AI tools — Claude, ChatGPT, Copilot, or anything else you normally use. What matters is not whether you use them, but how thoughtfully you use them. We will ask you to share your prompt log as part of your submission, so we can see what you asked and how you refined your approach.

---

## The Problem

You have been given a small Python web application. It accepts a plain-text receipt as input, sends it to an AI model, and is supposed to return a structured list of expense line items, each with a name, amount, and category.

### Example Input

```
Uber Eats       $34.20
AWS invoice     $412.00
Office Depot    $28.50
Delta Airlines  $890.00
```

### Expected Output

```json
[
  { "item": "Uber Eats",      "amount": 34.20,  "category": "meals" },
  { "item": "AWS invoice",    "amount": 412.00, "category": "software" },
  { "item": "Office Depot",   "amount": 28.50,  "category": "office_supplies" },
  { "item": "Delta Airlines", "amount": 890.00, "category": "travel" }
]
```

The valid categories are: `meals`, `travel`, `software`, `office_supplies`, and `other`.

The current implementation does not reliably produce this output. It sends the receipt to the model and returns the raw response as a string, with no structure, no validation, and no error handling. If the model responds in an unexpected format — which it will — the application either crashes or silently returns garbage.

**Your job is to make it meaningfully more reliable.**

---

## The Starting Code

See [`scaffold.py`](./scaffold.py) in this repository.

You are free to restructure this code however you like. You are not required to keep FastAPI or any of the existing structure if you have a good reason to change it.

---

## What to Do

The most important problem in this scaffold is that **model output is trusted without validation**. Start there.

Once you've addressed that issue, make any additional reliability improvements you believe are worthwhile within the time available.

We do not expect a production-ready solution. We are more interested in your prioritization and tradeoff decisions than in the number of features you implement.

### Examples of meaningful improvements (rough priority order):

1. **Make the output structured and validated**
   - Update the prompt so the model returns JSON in a predictable schema
   - Parse the response and validate it before returning it to the caller
   - Return a clear, structured error if the response cannot be parsed

2. **Handle failure cases explicitly**
   - Handle model API errors rather than letting them propagate as unhandled exceptions
   - Handle the case where the model returns something that cannot be parsed
   - Return a response that tells the caller what went wrong, not just a 500 error

3. **Add a retry with a corrective prompt**
   - If the first response cannot be parsed, retry once with a prompt that includes the bad response and asks the model to correct it
   - If the retry also fails, return a structured error

4. **Add observability**
   - Log the raw model response alongside the parsed result so failures can be diagnosed later
   - Log enough context to reconstruct what happened: the input, the raw response, and what failed

> **Where to start**
>
> If you are not sure where to begin, ask yourself: what happens if the model returns something unexpected? Trace that path through the current code. The most important problem will become obvious quickly.

---

## Time Guidance

| Phase | Time |
|-------|------|
| Read the scaffold. Identify the problems. Decide what to fix. | 10–15 min |
| Build your fix. Test with at least one example. Make sure it runs. | 35–45 min |
| Write your submission notes. Review your prompt log. | 10–15 min |

If you find yourself past 75 minutes, **stop building and write your submission notes**. An incomplete solution with clear notes is much better than an incomplete solution with no explanation.

---

## How to Submit

See [`SUBMISSION_GUIDE.md`](./SUBMISSION_GUIDE.md) for full instructions.

**Quick version:**
1. Clone this repo and build your solution
2. Add an `alias.txt` file with your chosen alias
3. Push to your own GitHub repo (public or private — we'll request access if needed)
4. Fill out the [submission form](https://docs.google.com/forms/d/e/1FAIpQLSdkL0DdPcMHnE6olvtK3gQvaza-sZN2EEzFyYG3uD91WhqjcA/viewform) with your alias and repo link

---

## What We Evaluate

| Area | What we're looking for |
|------|----------------------|
| **Problem identification** | Did you identify the right thing to fix? The structural issue — that model output is trusted without validation — not surface details. |
| **Execution** | Did you get something working? A narrow, finished fix is far better than a broad, incomplete one. |
| **Reliability thinking** | Does your solution handle unexpected model output? Good fixes treat model output as untrusted until validated. |
| **AI tool usage** | Did you prompt with intention? Did you check what came back? Can you explain what the tools produced? |

---

## What to Avoid

- Trying to fix every problem in the scaffold. Pick the most important one.
- Submitting code that does not run. Test with at least one example.
- Submitting code you cannot explain.
- Skipping the written note. It is required.
- Going over 90 minutes.

---

## Next Steps

If your submission is strong, we will reach out to schedule a short follow-up call. On that call, we will ask you to walk through your solution, explain your decisions, and discuss what you would improve with more time.

There are no trick questions and no expectation of perfection. We are looking for candidates who can think clearly, communicate well, and build something real under reasonable constraints.
