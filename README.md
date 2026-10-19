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

## ✨ Features

- **Sorting by time:** tasks are ordered by their "HH:MM" time, earliest first, with untimed tasks last. Times are compared as numbers, so "9:05" sorts before "12:00".
- **Priority ordering:** the daily plan takes high-priority tasks first, then earlier preferred time, then shorter tasks.
- **Filtering:** view tasks by pet, by completion status (pending or completed), or both.
- **Conflict warnings:** tasks set for the exact same date and time trigger a warning, whether they belong to the same pet or different pets. It's a warning, never a crash.
- **Daily and weekly recurrence:** completing a daily task creates the next one for the following day, and a weekly task for the same weekday a week or more later. The new task is never scheduled in the past, even if the old one was overdue.
- **Next free slot:** find the earliest time today where a task of a given length fits, counting how long existing tasks last so overlaps are avoided.
- **Saved data:** pets and tasks are saved to `data.json` and come back when you restart the app.
- **Time-budget planning:** tasks are fit into the owner's available time. Anything that doesn't fit is skipped with a reason, and smaller tasks can still fill the gap.
- **Plan explanations:** every plan says how much time was used, what was skipped, and why.
- **Due-date awareness:** only tasks due today or earlier appear in today's plan, so tomorrow's recurring tasks stay out.
- **Color-coded output:** emoji for task types and colored priority and status in the terminal (`--pretty`) and the app.
- **Input validation:** empty descriptions, non-positive durations, unknown priorities or frequencies, malformed "HH:MM" times, and negative available time are rejected with clear errors.

## Implementation summary

The core logic lives in `diagrams/pawpal_system.py` and is built from a few small classes (the final UML is in `diagrams/uml_final.mmd`):

- **Task** (dataclass): one care activity with a description, duration, priority, optional preferred time, frequency (once/daily/weekly), and completion status. It validates its inputs and can be marked complete.
- **Pet** (dataclass): stores a pet's name and species plus its list of tasks. Adding a task tags it with the pet's name.
- **Owner** (dataclass): holds the owner's available minutes and manages multiple pets. `get_all_tasks()` returns every pet's tasks together in one list.
- **Scheduler**: the brain. It reads tasks through `owner.get_all_tasks()` (never from a single pet), skips completed ones, sorts by priority, then preferred time, then shortest first, and fits them into the owner's available time.
- **Plan / ScheduledTask** (dataclasses): the scheduler's output. A plan holds the scheduled tasks (each with a start and end minute) and the skipped tasks with the reason each didn't fit, which `explain_plan()` turns into text.

**How they work together:** `Owner` has many `Pet`s, each `Pet` has many `Task`s. A `Scheduler` is given an `Owner`, pulls all of its tasks, and produces a `Plan`. `diagrams/main.py` is a demo script that builds an owner with three pets and prints the results to the terminal, and the Streamlit UI in `app.py` lets a user do the same interactively.

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

A generated daily plan from `python3 diagrams/main.py` (the full run is in the Demo Walkthrough below):

```
Today's Schedule for Jason
----------------------------------------
0-5 min: Give meds (Luna, high, 5 min)
5-20 min: Vet call (Biscuit, medium, 15 min)
20-40 min: Evening play (Biscuit, low, 20 min)
40-55 min: Playtime (Luna, low, 15 min)
55-60 min: Brush fur (Luna, low, 5 min)
----------------------------------------
Total: 60/90 min
```

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

(On a machine where `python` isn't available, use `python3 -m pytest`, or activate `.venv` first.)

The 71 tests in `tests/test_pawpal.py` cover the scheduler logic in `diagrams/pawpal_system.py`:

- **Basics:** marking a task complete, and adding a task to a pet.
- **Sorting:** chronological order by time, untimed tasks last, unpadded times like "9:05", ties keep their order, and priority/time/duration ordering for plans.
- **Filtering:** by completion status, by pet (case-insensitive), both together, and unknown or empty pets.
- **Recurring tasks:** daily is +1 day and weekly keeps its weekday, including month, year and leap-day rollovers; "once" tasks create nothing; no duplicates on repeat completion; completing a task the owner doesn't have raises an error.
- **Conflict detection:** same time for the same pet and across pets, three-way clashes, and no false alarms for completed tasks, untimed tasks, or the same time on different dates.
- **Plan generation:** tasks placed back to back, exact fits, skipping oversized tasks while smaller ones still fit, and empty cases (no pets, no tasks, all complete, zero available minutes).
- **Next free slot:** free day, gaps that fit and don't fit, overlapping tasks, full days, and ignored (completed, untimed, other-day) tasks.
- **Saving and loading:** a full round trip, ISO dates, overwriting, missing and corrupt files, and invalid data being rejected.
- **Formatting:** emoji, color codes, and the pretty tables.
- **Validation:** an empty description, bad duration, priority, frequency, malformed "HH:MM" times, and negative available time are rejected.
- **Regressions:** overdue recurring tasks never reschedule into the past, `explain_plan()` is never stale, and `remove_task()` removes the exact task.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/jasonyeh/CS/AI110-Pawpal
plugins: anyio-4.15.1
collected 71 items

tests/test_pawpal.py ................................................... [ 71%]
....................                                                     [100%]

============================== 71 passed in 0.07s ==============================
```

**Confidence Level: ⭐⭐⭐⭐ (4/5)**

All 71 tests pass, and they cover the happy paths and the main edge cases for sorting, filtering, recurrence, conflicts and planning. They also caught a real bug (malformed times were accepted) before it reached the UI. I stopped at four stars because the Streamlit UI was only checked with a headless run, not automated tests, conflict detection only flags exact time matches (not overlapping durations), and the greedy planner's tradeoffs are covered by only a few cases.

## 📐 Smarter Scheduling

All of this lives in `diagrams/pawpal_system.py`.

- **Sorting:** `Scheduler.sort_by_time()` orders tasks by their "HH:MM" time, earliest first, with untimed tasks last. `Scheduler.sort_tasks()` orders by priority, then time, then shortest.
- **Filtering:** `Scheduler.filter_tasks()` keeps tasks by completion status, by pet name, or both.
- **Conflict detection:** `Scheduler.detect_conflicts()` returns warnings for tasks at the exact same date and time. It never raises an error.
- **Recurring tasks:** `Scheduler.mark_task_complete()` creates the next daily (+1 day) or weekly (same weekday, at least 7 days later) task using `Task.next_occurrence()`.
- **Next free slot:** `Scheduler.find_next_available_slot()` returns the earliest "HH:MM" today where a task of a given length fits between existing tasks.
- **Planning:** `Scheduler.generate_plan()` fits due tasks into the available time, and `explain_plan()` says why.

## 🎯 Priority Scheduling

Every task has a priority: `low`, `medium` or `high`. The plan takes high-priority tasks first, then the earliest preferred time, then the shortest task (`Scheduler.sort_tasks()`). Sorting by time alone (`sort_by_time()`) ignores priority, so the two orders differ.

Output of `python3 diagrams/main.py`:

```
Sorted by time:
  07:30  Morning walk (Biscuit, high, todo)
  08:00  Breakfast (Luna, high, done)
  12:00  Vet call (Biscuit, medium, todo)
  12:00  Clean cage (Kiwi, medium, todo)
  18:30  Evening play (Biscuit, low, todo)
  19:00  Give meds (Luna, high, todo)
  19:00  Playtime (Luna, low, todo)
  --:--  Brush fur (Luna, low, todo)

Priority order (high first, then earliest time):
  07:30  Morning walk (Biscuit, high, todo)
  08:00  Breakfast (Luna, high, done)
  19:00  Give meds (Luna, high, todo)
  12:00  Vet call (Biscuit, medium, todo)
  12:00  Clean cage (Kiwi, medium, todo)
  18:30  Evening play (Biscuit, low, todo)
  19:00  Playtime (Luna, low, todo)
  --:--  Brush fur (Luna, low, todo)
```

Give meds (high) is at 19:00, but it is planned first, ahead of earlier low-priority tasks:

```
Today's Schedule for Jason
----------------------------------------
0-5 min: Give meds (Luna, high, 5 min)
5-20 min: Vet call (Biscuit, medium, 15 min)
20-40 min: Evening play (Biscuit, low, 20 min)
40-55 min: Playtime (Luna, low, 15 min)
55-60 min: Brush fur (Luna, low, 5 min)
----------------------------------------
Total: 60/90 min
```

## 💾 Data Persistence

Pets and tasks are saved to `data.json` so they are still there the next time you run the app.

- **When it loads:** the app reads `data.json` when it starts. If the file doesn't exist, it starts with a new owner.
- **When it saves:** after every action, such as adding a pet or task or marking a task complete.
- **Start over:** clears the app and deletes `data.json`.
- **Bad file:** if `data.json` can't be read, the app keeps a copy as `data.json.bak` and starts fresh.

How it works: `Owner.save_to_json()` and `Owner.load_from_json()` in `pawpal_system.py`. They use custom `to_dict()` and `from_dict()` methods on `Task`, `Pet` and `Owner` (dates are stored as ISO text like `2026-10-18`), so no extra library is needed. Loading rebuilds the objects through their constructors, so invalid data is rejected. Files are written to a temporary file and then swapped in, so a crash can't leave half a file.

Files modified: `diagrams/pawpal_system.py`, `app.py`, `.gitignore` (`data.json` is not committed).

Example from `python3 diagrams/main.py`:

```
Saving to JSON and loading it back:
  Saved 3 pets and 10 tasks
  Loaded 3 pets and 10 tasks, identical: True
```

## 🎨 Output Formatting

The terminal output is plain text by default so it is easy to copy. Add `--pretty` for tables with emoji and color:

```bash
pip install -r requirements.txt
python3 diagrams/main.py --pretty
```

- **Emoji for task types:** walks 🦮, meals 🍖, meds 💊, vet 🩺, grooming 🛁, play 🎾, cleaning 🧹, water 💧 (`task_icon()`).
- **Color-coded priority and status:** red, yellow and green priority, and a green "done" or yellow "to do" status (`priority_label()` and `status_label()`).
- **Tables:** built with the `tabulate` library (`format_tasks()` and `format_schedule()`).
- **In the app:** the task and schedule tables show the same emoji icons and priority colors.

All of these functions are in `diagrams/formatting.py`. Files modified: `diagrams/main.py`, `app.py`, `requirements.txt`. Sample output (colors are not shown here):

```
Today's Schedule for Jason
╭───────────┬─────────────────┬─────────┬────────────┬────────────╮
│ Minutes   │ Task            │ Pet     │ Priority   │   Duration │
├───────────┼─────────────────┼─────────┼────────────┼────────────┤
│ 0-5       │ 💊 Give meds    │ Luna    │ 🔴 high    │          5 │
├───────────┼─────────────────┼─────────┼────────────┼────────────┤
│ 5-20      │ 🩺 Vet call     │ Biscuit │ 🟡 medium  │         15 │
├───────────┼─────────────────┼─────────┼────────────┼────────────┤
│ 20-40     │ 🎾 Evening play │ Biscuit │ 🟢 low     │         20 │
├───────────┼─────────────────┼─────────┼────────────┼────────────┤
│ 40-55     │ 🎾 Playtime     │ Luna    │ 🟢 low     │         15 │
├───────────┼─────────────────┼─────────┼────────────┼────────────┤
│ 55-60     │ 🛁 Brush fur    │ Luna    │ 🟢 low     │          5 │
╰───────────┴─────────────────┴─────────┴────────────┴────────────╯
Total: 60/90 min
```

## 📸 Demo Walkthrough

Run the app with `streamlit run app.py`, or run the terminal demo with `python3 diagrams/main.py`.

### What you can do in the app

- **Owner:** set your name and how much time you have today, using hour and minute dropdowns (up to 7h 55m, in 5-minute steps).
- **Pets:** add as many pets as you like (name and species). Duplicate or empty names are rejected.
- **Tasks:** add a task for a pet with a description, duration, priority, frequency (once, daily, weekly), and an optional preferred time.
- **Task list:** sort by time, priority, or order added, and filter by pet and status. Time conflicts show up as warnings right above the list.
- **Mark complete:** finish a task; if it repeats, the next one is created automatically.
- **Find a free time slot:** pick a task length and get the earliest time today where it fits.
- **Generate schedule:** build today's plan, see what was skipped and why, and open "Why this plan?" for the explanation.
- **Start over:** clear everything and begin again. Your pets and tasks are saved to `data.json` automatically until you do.

### Example workflow

1. Set the owner's name and available time, for example 1 hour 30 minutes.
2. Add a pet, for example Biscuit the dog, then add a second pet, Luna the cat.
3. Add tasks, such as a 30-minute "Morning walk" (high, daily, 07:30) for Biscuit and a 10-minute "Breakfast" (high, daily, 08:00) for Luna.
4. Add a third task at the same time as one of the others. A warning appears: the two tasks can't both happen at that time, so change one.
5. Sort the list by time, then filter to just Luna's pending tasks.
6. Mark "Breakfast" complete and see that tomorrow's Breakfast is created.
7. Click **Generate schedule** to see today's plan and how much of your time it uses.

### Scheduler behaviors shown

- **Sorting:** tasks added out of order come back in time order, with untimed tasks last.
- **Filtering:** by pet, by completed, by pending, and by combinations of those.
- **Conflict warnings:** one clash between different pets (12:00) and one between tasks for the same pet (19:00).
- **Recurrence:** a completed daily task is due again the next day, and a weekly task a week later.
- **Next free slot:** the earliest time a task of a given length fits, counting existing durations.
- **Persistence:** the data is saved to JSON and loaded back unchanged.
- **Planning:** high-priority tasks go first, completed tasks are left out, and the plan stays within the available time.

### Sample CLI output

Output of `python3 diagrams/main.py` (dates reflect the day it was run):

```
All tasks, in the order added:
  18:30  Evening play (Biscuit, low, todo)
  07:30  Morning walk (Biscuit, high, todo)
  12:00  Vet call (Biscuit, medium, todo)
  08:00  Breakfast (Luna, high, done)
  --:--  Brush fur (Luna, low, todo)
  19:00  Give meds (Luna, high, todo)
  19:00  Playtime (Luna, low, todo)
  12:00  Clean cage (Kiwi, medium, todo)

Sorted by time:
  07:30  Morning walk (Biscuit, high, todo)
  08:00  Breakfast (Luna, high, done)
  12:00  Vet call (Biscuit, medium, todo)
  12:00  Clean cage (Kiwi, medium, todo)
  18:30  Evening play (Biscuit, low, todo)
  19:00  Give meds (Luna, high, todo)
  19:00  Playtime (Luna, low, todo)
  --:--  Brush fur (Luna, low, todo)

Priority order (high first, then earliest time):
  07:30  Morning walk (Biscuit, high, todo)
  08:00  Breakfast (Luna, high, done)
  19:00  Give meds (Luna, high, todo)
  12:00  Vet call (Biscuit, medium, todo)
  12:00  Clean cage (Kiwi, medium, todo)
  18:30  Evening play (Biscuit, low, todo)
  19:00  Playtime (Luna, low, todo)
  --:--  Brush fur (Luna, low, todo)

Only Biscuit's tasks:
  18:30  Evening play (Biscuit, low, todo)
  07:30  Morning walk (Biscuit, high, todo)
  12:00  Vet call (Biscuit, medium, todo)

Completed tasks:
  08:00  Breakfast (Luna, high, done)

Pending tasks:
  18:30  Evening play (Biscuit, low, todo)
  07:30  Morning walk (Biscuit, high, todo)
  12:00  Vet call (Biscuit, medium, todo)
  --:--  Brush fur (Luna, low, todo)
  19:00  Give meds (Luna, high, todo)
  19:00  Playtime (Luna, low, todo)
  12:00  Clean cage (Kiwi, medium, todo)

Luna's pending tasks, sorted by time:
  19:00  Give meds (Luna, high, todo)
  19:00  Playtime (Luna, low, todo)
  --:--  Brush fur (Luna, low, todo)

Conflict check:
  WARNING: Conflict across pets: 2 tasks at 12:00 on 2026-10-18: Vet call (Biscuit), Clean cage (Kiwi)
  WARNING: Conflict for Luna: 2 tasks at 19:00 on 2026-10-18: Give meds (Luna), Playtime (Luna)

Next available slot (counts task durations, completed tasks don't block):
  30 min, starting 07:00 or later -> 07:00
  60 min, starting 12:00 or later -> 12:25
  45 min, starting 18:00 or later -> 19:15

Completing a daily and a weekly task creates the next occurrence:
  Morning walk (daily, due 2026-10-18) -> next due 2026-10-19
  Clean cage (weekly, due 2026-10-18) -> next due 2026-10-25
  Biscuit now has 4 tasks, Kiwi has 2

Saving to JSON and loading it back:
  Saved 3 pets and 10 tasks
  Loaded 3 pets and 10 tasks, identical: True

Today's Schedule for Jason
----------------------------------------
0-5 min: Give meds (Luna, high, 5 min)
5-20 min: Vet call (Biscuit, medium, 15 min)
20-40 min: Evening play (Biscuit, low, 20 min)
40-55 min: Playtime (Luna, low, 15 min)
55-60 min: Brush fur (Luna, low, 5 min)
----------------------------------------
Total: 60/90 min
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
