# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation summary

The core logic lives in `diagrams/pawpal_system.py` and is built from a few small classes (the UML is in `diagrams/uml.mmd`):

- **Task** (dataclass): one care activity with a description, duration, priority, optional preferred time, frequency (once/daily/weekly), and completion status. It validates its inputs and can be marked complete.
- **Pet** (dataclass): stores a pet's name and species plus its list of tasks. Adding a task tags it with the pet's name.
- **Owner** (dataclass): holds the owner's available minutes and manages multiple pets. `get_all_tasks()` returns every pet's tasks together in one list.
- **Scheduler**: the brain. It reads tasks through `owner.get_all_tasks()` (never from a single pet), skips completed ones, sorts by priority, then preferred time, then shortest first, and fits them into the owner's available time.
- **Plan / ScheduledTask** (dataclasses): the scheduler's output. A plan holds the scheduled tasks (each with a start and end minute) and the skipped tasks with the reason each didn't fit, which `explain_plan()` turns into text.

**How they work together:** `Owner` has many `Pet`s, each `Pet` has many `Task`s. A `Scheduler` is given an `Owner`, pulls all of its tasks, and produces a `Plan`. `diagrams/main.py` is a demo script that builds an owner with three pets and prints the day's schedule. The Streamlit UI in `app.py` is not connected yet.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Today's Schedule for Jason
----------------------------------------
0-30 min: Morning walk (Biscuit, high, 30 min)
30-40 min: Breakfast (Luna, high, 10 min)
40-65 min: Clean cage (Kiwi, medium, 25 min)
65-85 min: Evening play (Biscuit, low, 20 min)
----------------------------------------
Total: 85/90 min

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

Every feature below lives in `diagrams/pawpal_system.py` and reads tasks through the `Owner`.

| Feature | Method(s) | What it does |
|---------|-----------|--------------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders tasks by preferred "HH:MM" time, earliest first, with untimed tasks last. Times are compared as minutes (via `to_minutes()`), so "9:05" correctly sorts before "12:00". |
| Sorting for the plan | `Scheduler.sort_tasks()` | Orders by priority (high first), then preferred time, then shortest duration. |
| Filtering | `Scheduler.filter_tasks(completed=, pet_name=)` | Keeps only done or not-done tasks, and/or one pet's tasks (case-insensitive). Both filters can be combined. Also see `get_pending_tasks()` and `get_tasks_for_pet()`. |
| Fitting to available time | `Scheduler.generate_plan()` | Greedily places due, pending tasks in sorted order until the owner's time runs out. Tasks that don't fit are skipped with a reason, and smaller tasks can still fill the gap. `explain_plan()` describes the result. |
| Conflict detection | `Scheduler.detect_conflicts()` | Flags pending tasks that share the exact same date and preferred time, for the same pet or across pets. Returns warning strings instead of raising errors; an empty list means no conflicts. Overlapping durations are not checked. |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete()` | Completing a "daily" task creates a new copy due +1 day, and a "weekly" task +7 days (using `timedelta`). "once" tasks create nothing. `Scheduler.get_due_tasks()` keeps future occurrences out of today's plan. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
