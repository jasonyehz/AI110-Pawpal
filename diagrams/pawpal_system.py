from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    completed: bool = False
    pet_name: str = ""

    def mark_complete(self) -> None:
        pass


@dataclass
class ScheduledTask:
    task: Task
    start_minute: int

    @property
    def end_minute(self) -> int:
        return self.start_minute + self.task.duration_minutes


@dataclass
class Plan:
    scheduled: List[ScheduledTask] = field(default_factory=list)
    skipped: List[Tuple[Task, str]] = field(default_factory=list)


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> List[Task]:
        raise NotImplementedError


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: Optional[Plan] = None

    def generate_plan(self) -> Plan:
        raise NotImplementedError

    def explain_plan(self) -> str:
        raise NotImplementedError
