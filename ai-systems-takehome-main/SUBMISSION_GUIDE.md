# Submission Guide

## Step 1: Build Your Solution

1. Clone or fork this repository
2. Read `scaffold.py` and the problem statement in `README.md`
3. Build your fix — restructure however you like
4. Test it with at least one example input to confirm it runs

## Step 2: Choose Your Alias

Create a file called `alias.txt` in the root of your repo containing a single line: your chosen alias for the leaderboard.

```
# Example alias.txt
phantom_engineer
```

**Rules:**
- One word or two words joined by underscore
- No real names or identifying info
- Keep it tasteful
- First come, first served — if your alias is taken, we'll ask you to pick another

## Step 3: Include Your Prompt Log

Create a file called `PROMPT_LOG.md` (or `prompt_log.txt`, or a folder of screenshots) containing the prompts you used with AI tools during the assignment.

We want to see:
- What you asked
- How you refined your approach
- What you accepted vs. what you changed

Format doesn't matter — plain text, markdown, screenshots all work.

## Step 4: Write Your Submission Notes

Create a file called `NOTES.md` with a short writeup (half a page or less). Cover:

- What you identified as the most important problem and why
- What you built and what you deliberately left out
- Where your solution would still break, and what you would fix next with more time
- How you used AI tools, and anything you checked or changed before trusting their output

Bullet points are fine. We're looking for clear thinking, not polished prose.

## Step 5: Push & Submit

1. Push your completed solution to your own GitHub repository
2. Fill out the submission form: **[Submit here](https://docs.google.com/forms/d/e/1FAIpQLSdkL0DdPcMHnE6olvtK3gQvaza-sZN2EEzFyYG3uD91WhqjcA/viewform)**
   - Your alias (must match `alias.txt`)
   - Link to your GitHub repo
   - (Optional) Link to a demo video or recording

## Your Repo Should Contain

```
your-repo/
├── alias.txt              # Your leaderboard alias
├── NOTES.md               # Your written submission notes
├── PROMPT_LOG.md          # Your AI tool prompt history
├── scaffold.py            # Your modified/replaced code (or new files)
├── requirements.txt       # Dependencies (if any beyond the scaffold)
└── demo/                  # (Optional) screenshots, video link, or demo output
    └── example_output.json
```

## Optional: Include a Demo

If you want to showcase your solution working, include one of:
- A short video (Loom, screen recording) linked in your NOTES.md
- A `demo/` folder with example input/output showing your solution in action
- A GIF or screenshot of it running

This is optional but helps your submission stand out on the leaderboard.

---

## The Leaderboard

All submissions will appear on the leaderboard by alias. Scores are posted across 4 axes:

| Axis | Description |
|------|-------------|
| 🎯 Problem ID | Did you find the right thing to fix? |
| ⚡ Execution | Does it work? Is it clean? |
| 🛡️ Reliability | Does it handle the unexpected? |
| 🤖 AI Usage | Did you use tools thoughtfully? |

Each axis is scored 1–5. Your total score and ranking will be visible to all participants (by alias only).

---

## Timeline

- **Submission deadline:** [TBD]
- **Leaderboard posted:** Within 48 hours of deadline
- **Follow-up calls:** Scheduled within 1 week for strong submissions

## Questions?

If something in the problem statement is genuinely ambiguous, use your best judgment and document your assumption in `NOTES.md`. That's part of what we're evaluating.
