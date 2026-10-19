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

Run the full test suite from the project root:

```bash
python -m pytest
```

(On a machine where `python` isn't available, use `python3 -m pytest`, or activate `.venv` first.)

The 47 tests in `tests/test_pawpal.py` cover the scheduler logic in `diagrams/pawpal_system.py`:

- **Basics:** marking a task complete, and adding a task to a pet.
- **Sorting:** chronological order by time, untimed tasks last, unpadded times like "9:05", ties keep their order, and priority/time/duration ordering for plans.
- **Filtering:** by completion status, by pet (case-insensitive), both together, and unknown or empty pets.
- **Recurring tasks:** daily is +1 day and weekly is +7 days, including month, year and leap-day rollovers; "once" tasks create nothing; no duplicates on repeat completion; completing a task the owner doesn't have raises an error.
- **Conflict detection:** same time for the same pet and across pets, three-way clashes, and no false alarms for completed tasks, untimed tasks, or the same time on different dates.
- **Plan generation:** tasks placed back to back, exact fits, skipping oversized tasks while smaller ones still fit, and empty cases (no pets, no tasks, all complete, zero available minutes).
- **Validation:** an empty description, bad duration, priority, frequency, malformed "HH:MM" times, and negative available time are rejected.
- **Regressions:** overdue recurring tasks never reschedule into the past, `explain_plan()` is never stale, and `remove_task()` removes the exact task.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/jasonyeh/CS/AI110-Pawpal
plugins: anyio-4.15.1
collected 47 items

tests/test_pawpal.py ...............................................     [100%]

============================== 47 passed in 0.03s ==============================
```

**Confidence Level: ⭐⭐⭐⭐ (4/5)**

All 47 tests pass, and they cover the happy paths and the main edge cases for sorting, filtering, recurrence, conflicts and planning. They also caught a real bug (malformed times were accepted) before it reached the UI. I stopped at four stars because the Streamlit UI was only checked with a headless run, not automated tests, conflict detection only flags exact time matches (not overlapping durations), and the greedy planner's tradeoffs are covered by only a few cases.

## 📐 Smarter Scheduling

All of this lives in `diagrams/pawpal_system.py`.

- **Sorting:** `Scheduler.sort_by_time()` orders tasks by their "HH:MM" time, earliest first, with untimed tasks last. `Scheduler.sort_tasks()` orders by priority, then time, then shortest.
- **Filtering:** `Scheduler.filter_tasks()` keeps tasks by completion status, by pet name, or both.
- **Conflict detection:** `Scheduler.detect_conflicts()` returns warnings for tasks at the exact same date and time. It never raises an error.
- **Recurring tasks:** `Scheduler.mark_task_complete()` creates the next daily (+1 day) or weekly (+7 days) task using `Task.next_occurrence()`.
- **Planning:** `Scheduler.generate_plan()` fits due tasks into the available time, and `explain_plan()` says why.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
