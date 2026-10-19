from dataclasses import dataclass, field
from typing import List, Optional, Tuple

PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("once", "daily", "weekly")


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

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """All tasks belonging to the pet with the given name."""
        return [t for t in self.owner.get_all_tasks() if t.pet_name == pet_name]

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Highest priority first, then earliest preferred time, then shortest."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority_rank,
                t.time is None,
                t.time or "",
                t.duration_minutes,
            ),
        )

    def generate_plan(self) -> Plan:
        """Greedily fit pending tasks into the owner's available time."""
        plan = Plan()
        cursor = 0
        budget = self.owner.available_minutes

        for task in self.sort_tasks(self.get_pending_tasks()):
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
