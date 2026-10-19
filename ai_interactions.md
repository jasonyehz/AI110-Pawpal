# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

**What task did you give the agent?**

Extend PawPal+ with five stretch features in one multi-step job: a third algorithm (next available slot), saving data to `data.json`, priority-based scheduling shown in CLI output, color and emoji output with `tabulate`, and a comparison of two models on a rescheduling algorithm. I also asked for the README sections to stay short and simple.

**What did the agent do?**

Files modified or added, and what changed in each:

| File | Change |
|------|--------|
| `diagrams/pawpal_system.py` | Added `Scheduler.find_next_available_slot()`, `to_dict()`/`from_dict()` on `Task`, `Pet` and `Owner`, `Owner.save_to_json()` and `Owner.load_from_json()`, and a weekday-preserving `Task.next_occurrence()` |
| `diagrams/formatting.py` (new) | Emoji, ANSI colors, and `tabulate` tables |
| `diagrams/main.py` | `--pretty` flag, priority order, next-slot and save/load demos |
| `app.py` | Loads and saves `data.json`, "Find a free time slot" tool, emoji icons, Start over deletes the file |
| `tests/test_pawpal.py` | 24 new tests (71 in total) |
| `README.md` | Short sections for priority scheduling, persistence, and formatting; updated sample outputs |
| `requirements.txt`, `.gitignore` | Added `tabulate[widechars]`; ignored `data.json` |

Steps it took: ran two models on the same prompt in the background, tested both against a brute-force reference, wrote the code, installed `tabulate` into `.venv`, ran the tests, and ran the app in Streamlit's headless test runner against a temporary copy so my real data file was never touched.

**What did you have to verify or fix manually?**

- **README wording:** I asked for the new sections to be simple and straightforward, and I reviewed and adjusted the README text myself.
- **`tabulate` wasn't installed:** it was installed into `.venv`, and `--pretty` prints a clear message instead of a traceback if it's missing. Plain output stays the default so it copies and pastes cleanly.
- **A broken `.gitignore`:** the agent's first append ran onto the last line (the file had no trailing newline) and created a bogus `.DS_Storedata.json` entry. It was caught in review and fixed.
- **Nothing written on a failed edit:** one scripted README edit stopped at a wording mismatch (I had edited that line). The agent re-read the file and reran it.
- **Test-script mistakes:** a widget label typo was a mistake in the test, not the app.
- **Real data protected:** app tests ran on a temporary copy so they could not overwrite a real `data.json`.

---

## Prompt Comparison (SF11)

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Opus (model chosen with the Agent tool) | Claude Haiku (model chosen with the Agent tool) |
| **Prompt** | Same prompt for both: write `Task.next_occurrence(today)`. Daily is `max(due, today) + 1 day`. Weekly must keep the same weekday, be strictly after today, and be at least 7 days after the old due date. Handle month, year and leap-year rollovers, and don't mutate the task. Three worked examples were included. | Identical |
| **Response summary** | Computes the number of whole weeks to add: `weeks = max(1, (today - due).days // 7 + 1)`, then `due + weeks`. Also normalizes the frequency with `.strip().lower()` and adds a docstring. | Computes a lower bound `max(due + 7, today + 1)`, then adds the days needed to land on the original weekday: `(due.weekday() - earliest.weekday()) % 7`. |
| **What was useful** | Correct, with a clear docstring and a good explanation of the week-boundary case. | Correct, shorter, and each line matches one rule from the prompt. |
| **Problems noticed** | Relies on floor division and `max(1, ...)` to handle negative values, which is hard to see at a glance. Normalizing the frequency is redundant because `Task` already does that. | No docstring, and it doesn't explain the week-boundary edge case. |
| **Decision** | Not used as written | Used (the logic) |

I ran both solutions and my own earlier version against a brute-force reference on 112,980 date combinations. Opus and Haiku had 0 mismatches. My earlier version, which added 7 days to the later of the due date and today, was wrong in 27,438 cases: a weekly task completed late moved to a different weekday (a Monday task done on Thursday came back on Thursday).

**Which approach did you use in your final implementation and why?**

I used the Haiku-style logic in `Task.next_occurrence()`, with an explicit `today` parameter so it is easy to test. Both models were correct, so I chose on readability: "lower bound, then line up the weekday" reads like the rules, while the floor-division version needs more thought to check. I left out the extra frequency normalizing since `Task` already does it. This also fixed a real bug in my earlier version.

Limit of this comparison: both are Claude models, so the comparison is not independent across companies. I could only call Claude models from this tool and did not have access to Gemini or ChatGPT.
