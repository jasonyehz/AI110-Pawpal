# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design will have four classes:
Owner: Holds information about the pet's owner and availability.
Pet: Holds information about the pet and its tasks
Task: Holds information about the type of task, duration, priotiy and can be marked complete.
Scheduler: The planning logic that makes schedules that work for everyone.

**b. Design changes**

I asked Claude to check if my skeleton's logic made sense and it identified a couple issues. First, my task class doesn't know specific pets as it flattens tasks across all pets. The solution was to add a pet_name or pet field on task and return (pet, task) pairs.
Additionally, tasks had durations but no start times, so the daily plan is merely an ordered list. The solution was to created a start_time function.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

My conflict detection only flags tasks that share the exact same date and preferred time (for example, two tasks at 19:00). It does not check overlapping durations, so a 30-minute walk at 08:00 and a feeding at 08:15 are not flagged even though they overlap. It also only returns warning messages; it never blocks a task or reschedules anything.

This is reasonable for PawPal+ because a preferred time is a loose preference, not a hard appointment, and the plan itself is built from durations and available minutes, so tasks never actually overlap in the generated schedule. An exact-match check is a single pass over the tasks, is easy to read and test, and catches the most obvious mistake (double-booking the same moment) without making the app complicated. A full interval-overlap check would be more precise, but it adds more code and edge cases than a simple pet-care planner needs.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
