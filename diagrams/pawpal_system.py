from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import List, Optional, Tuple

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")


def to_minutes(hhmm: str) -> int:
    """Convert an "HH:MM" string to minutes since midnight (e.g. "09:30" -> 570)."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


@dataclass
class Task:
    """A single pet-care activity."""

    description: str
    duration_minutes: int
    priority: str = "medium"
    time: Optional[str] = None  # preferred time of day, "HH:MM"
    frequency: str = "once"  # once | daily | weekly
    completed: bool = False
    pet_name: str = ""
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Normalize priority and frequency, and reject invalid values."""
        self.priority = self.priority.lower()
        self.frequency = self.frequency.lower()
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be one of {list(PRIORITY_RANK)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")

    @property
    def priority_rank(self) -> int:
        """Numeric priority (low=1, medium=2, high=3) used for sorting."""
        return PRIORITY_RANK[self.priority]

    def mark_complete(self) -> None:
        """Mark the task as done."""
        self.completed = True

    def next_occurrence(self) -> Optional["Task"]:
        """Build the next occurrence of a recurring task.

        Daily tasks are due 1 day later and weekly tasks 7 days later, using
        ``timedelta`` so month and year rollovers are handled correctly. The copy is
        not completed and keeps the pet name. Returns None for "once" tasks.
        """
        step = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}.get(self.frequency)
        if step is None:
            return None
        return replace(self, completed=False, due_date=self.due_date + step)

    def reset(self) -> None:
        """Mark the task as not done, e.g. when a recurring task comes around again."""
        self.completed = False


@dataclass
class ScheduledTask:
    task: Task
    start_minute: int  # minutes from the start of the day's plan

    @property
    def end_minute(self) -> int:
        """Minute at which this task finishes."""
        return self.start_minute + self.task.duration_minutes


@dataclass
class Plan:
    scheduled: List[ScheduledTask] = field(default_factory=list)
    skipped: List[Tuple[Task, str]] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Total duration of all scheduled tasks."""
        return sum(item.task.duration_minutes for item in self.scheduled)


@dataclass
class Pet:
    """Stores a pet's details and its list of tasks."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet."""
        self.tasks.remove(task)


@dataclass
class Owner:
    """Manages multiple pets and gives access to all of their tasks."""

    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Every task from every pet, together in one list."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The brain: retrieves, organizes, and manages tasks across all pets.

    It always reads tasks through the Owner (owner.get_all_tasks()), never
    from a single Pet.
    """

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans for the given owner."""
        self.owner = owner
        self.plan: Optional[Plan] = None

    def get_pending_tasks(self) -> List[Task]:
        """All tasks across the owner's pets that are not yet completed."""
        return [t for t in self.owner.get_all_tasks() if not t.completed]

    def get_due_tasks(self, on: Optional[date] = None) -> List[Task]:
        """Pending tasks due on or before the given date (default: today).

        Used by generate_plan() so a recurring task's next occurrence (due in the
        future) does not show up in today's plan.
        """
        on = on or date.today()
        return [t for t in self.get_pending_tasks() if t.due_date <= on]

    def detect_conflicts(self, tasks: Optional[List[Task]] = None) -> List[str]:
        """Lightweight conflict check that returns warning messages instead of raising.

        Groups pending tasks that have a preferred time by (due date, time in minutes)
        in a single pass. Any group with 2+ tasks produces one warning that says whether
        the clash is for one pet or across pets. Only exact matches are detected;
        overlapping durations are not checked. Returns an empty list when clear.
        """
        if tasks is None:
            tasks = self.get_pending_tasks()
        slots = defaultdict(list)
        for t in tasks:
            if t.time and not t.completed:
                slots[(t.due_date, to_minutes(t.time))].append(t)

        warnings = []
        for (due, minute), group in sorted(slots.items()):
            if len(group) > 1:
                pets = {t.pet_name for t in group}
                scope = f"for {pets.pop()}" if len(pets) == 1 else "across pets"
                names = ", ".join(f"{t.description} ({t.pet_name})" for t in group)
                warnings.append(
                    f"Conflict {scope}: {len(group)} tasks at {minute // 60:02d}:{minute % 60:02d} "
                    f"on {due}: {names}"
                )
        return warnings

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete and schedule its next occurrence if it recurs.

        Finds the pet that owns the task, completes it, and for daily/weekly tasks
        adds the next occurrence (see Task.next_occurrence) to that same pet.
        Returns the new task, or None if nothing was created (a "once" task, or a
        task that was already complete). Raises ValueError if the task isn't one of
        this owner's tasks.
        """
        pet = next((p for p in self.owner.pets if any(t is task for t in p.tasks)), None)
        if pet is None:
            raise ValueError("Task does not belong to any of this owner's pets")
        if task.completed:
            return None  # already done, so don't spawn a duplicate
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """All tasks belonging to the pet with the given name."""
        return [t for t in self.owner.get_all_tasks() if t.pet_name == pet_name]

    def filter_tasks(
        self, completed: Optional[bool] = None, pet_name: Optional[str] = None
    ) -> List[Task]:
        """Filter tasks across all pets by completion status and/or pet name.

        Reads tasks through the owner. ``completed=True/False`` keeps only done/not-done
        tasks, ``pet_name`` keeps one pet's tasks (case-insensitive), and passing both
        applies both filters. With no arguments every task is returned.
        """
        tasks = self.owner.get_all_tasks()
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name.lower() == pet_name.lower()]
        return tasks

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Order tasks for planning: highest priority first.

        Ties break by earliest preferred time (tasks without a time go last), then by
        shortest duration.
        """
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority_rank,
                t.time is None,
                to_minutes(t.time) if t.time else 0,
                t.duration_minutes,
            ),
        )

    def sort_by_time(self, tasks: Optional[List[Task]] = None) -> List[Task]:
        """Sort tasks by preferred "HH:MM" time, earliest first, untimed tasks last.

        Uses sorted() with a lambda key of (has no time, minutes since midnight). Times
        are compared as numbers, not strings, so "9:05" correctly sorts before "12:00".
        Defaults to all of the owner's tasks when no list is given.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(
            tasks,
            key=lambda t: (t.time is None, to_minutes(t.time) if t.time else 0),
        )

    def generate_plan(self) -> Plan:
        """Greedily fit due, pending tasks into the owner's available time.

        Tasks are taken in sort_tasks() order. Each is placed back to back if it fits in
        the remaining minutes; otherwise it is skipped with a reason and later, smaller
        tasks can still fill the gap. The result is stored in self.plan and returned.
        """
        plan = Plan()
        cursor = 0
        budget = self.owner.available_minutes

        for task in self.sort_tasks(self.get_due_tasks()):
            if cursor + task.duration_minutes <= budget:
                plan.scheduled.append(ScheduledTask(task, cursor))
                cursor += task.duration_minutes
            else:
                remaining = budget - cursor
                plan.skipped.append(
                    (
                        task,
                        f"needs {task.duration_minutes} min but only "
                        f"{remaining} min left",
                    )
                )

        self.plan = plan
        return plan

    def explain_plan(self) -> str:
        """Describe the plan in plain text, including skipped tasks and why."""
        plan = self.plan if self.plan is not None else self.generate_plan()

        lines = [
            f"Plan for {self.owner.name}: {plan.total_minutes} of "
            f"{self.owner.available_minutes} min used."
        ]
        for item in plan.scheduled:
            t = item.task
            lines.append(
                f"  {item.start_minute:>3}-{item.end_minute:<3} min  "
                f"{t.description} ({t.pet_name}) - {t.priority} priority, "
                f"{t.frequency}"
            )
        if plan.skipped:
            lines.append("Skipped:")
            for task, reason in plan.skipped:
                lines.append(f"  {task.description} ({task.pet_name}): {reason}")
        lines.append(
            "Tasks are ordered by priority, then preferred time, then shortest first."
        )
        return "\n".join(lines)
