# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design will have four classes:

Owner: Holds information about the pet's owner and availability.
Pet: Holds information about the pet and its tasks
Task: Holds information about the type of task, duration, priority and can be marked complete.
Scheduler: The planning logic that makes schedules that work for everyone.

**b. Design changes**

I asked Claude to check if my skeleton's logic made sense and it identified a couple issues. First, my task class doesn't know specific pets as it flattens tasks across all pets. The solution was to add a pet_name or pet field on task and return (pet, task) pairs.

Additionally, tasks had durations but no start times, so the daily plan is merely an ordered list. The solution was to created a start_time function.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four things: the owner's available time, each task's priority, an optional preferred time of day, and whether a task is due.

Available time is the one hard limit: a plan can never use more minutes than the owner has. Priority came next, because skipping a high-priority task like medication is worse than doing a walk at the wrong time, so tasks are ordered by priority first. The preferred time is only a tie-breaker between tasks of the same priority, and conflicting times only produce a warning instead of blocking anything.

**b. Tradeoffs**

One issue I noticed was that my conflict detection only flags tasks that share the exact same date and preferred time (for example, two tasks at 19:00). It does not check overlapping durations, so a 30-minute walk at 08:00 and a feeding at 08:15 are not flagged even though they overlap. It also only returns warning messages, and it never blocks a task or reschedules anything.

This is reasonable for pawpal because a preferred time is not set in stone, and the plan itself is built from durations and available minutes, so tasks never actually overlap in the generated schedule. An exact-match check is a single pass over the tasks, is easy to read and test, and catches the most obvious mistake without making the app complicated. A full interval-overlap check would be more precise, but it adds more code and edge cases than a simple pet-care planner needs.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude inside VS Code for a good portion of this assignment. Use cases includes drafting the Mermaid UML from my class ideas, generating the class skeleton, reviewing that skeleton for missing relationships, implementing the scheduling logic, wiring up the Streamlit app, writing tests, and updating the docs.

The most effective features were the ones that worked directly in my project. It could read my files and edit several of them in one change. It could also run the code and tests in the terminal to check its own work. Asking it to review my skeleton for "missing relationships and logic bottlenecks" gave me useful design fixes before I wrote any logic, and asking for a list of edge cases led to tests that found real bugs.

I worked in one long chat rather than separate sessions, so I kept it organized by phase instead: UML first, then class stubs, then logic, then tests, then the UI, then documentation, with the files updated at the end of each phase. The next time I would try a fresh session for testing, because a clean context makes it easier to review the code with fresh eyes.

**b. Judgment and verification**

When Claude first made the terminal schedule, it printed a fancy bordered table with emoji icons. I didn't like that. The emoji threw the columns out of line, and it was hard to copy and paste. I asked for a simpler plain-text version instead, which was clearer and easier to share. I made the same kind of call when I asked for the Smarter Scheduling section in the README to be simpler and shorter.

I verified suggestions by running them, not by trusting them. I ran `main.py` and the app after each change, and I asked Claude to keep testing for bugs. That found real problems that looked fine on reading, such as a time field that accepted "abc" until it crashed during sorting, an overdue daily task that created another overdue task, and an explanation that went stale after tasks changed. Each one got a test so it can't come back.

---

## 4. Testing and Verification

**a. What you tested**

I asked Claude to run 47 tests in `tests/test_pawpal.py` which covered the main scheduler behaviors:

- **Sorting:** tasks come back in time order, untimed tasks last, and times like "9:05" sort correctly.
- **Filtering:** by pet and by completion status, including unknown pets and empty lists.
- **Recurring tasks:** a completed daily task creates one for the next day and a weekly task one for 7 days later, including month, year and leap-day rollovers, and never creates duplicates.
- **Conflict detection:** same time for one pet and across pets, with no false alarms for completed, untimed, or different-day tasks.
- **Plan generation:** tasks fit the available time, oversized tasks are skipped with a reason, and empty cases give an empty plan.
- **Validation:** bad durations, priorities, frequencies, times, and negative available time are rejected.

**b. Confidence**

I'm fairly confident, about 4 out of 5. All 47 tests pass, and I also ran a randomized check on thousands of generated schedules that confirmed the plan never goes over the available time, never overlaps, and never loses or duplicates a task. I knocked down one star because the Streamlit UI was only checked with a headless run, and the conflict check only catches exact time matches.

With more time I would test overlapping durations (a 30-minute task at 08:00 and another at 08:15), the app's buttons with automated UI tests, the app running across midnight, and the same task object being added to two pets.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the structure. Each class has one job, and the Scheduler only reads tasks through `Owner.get_all_tasks()`, so the Streamlit app, the terminal script, and the tests all use the same logic. I'm also glad the test suite caught real bugs before they reached the app.

**b. What you would improve**

I would add real overlap detection, let users edit and delete tasks in the app, and save data to a file so it survives a browser refresh. I would also make the plan use clock times instead of minute offsets from the start of the day, and replace the string priorities with an enum so invalid values can't exist at all.

**c. Key takeaway**

Claude was extremely helpful in this project. It was fast and often added useful extras, like a `Plan` class so the explanation had something to explain, but each addition changes the design, so I had to decide what belonged and what was too much.

The other lesson is that AI output is not finished until it's verified. Code that looked right still had bugs that only tests found, so I treat every suggestion as a draft, and check it multiple times before committing.
