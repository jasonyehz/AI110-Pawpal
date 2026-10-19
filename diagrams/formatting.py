"""Optional pretty output for PawPal+: emoji, color-coded status, and tabulate tables."""

from typing import List

try:
    from tabulate import tabulate
except ImportError:  # tabulate is only needed for the --pretty tables
    tabulate = None

PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}
PRIORITY_COLOR = {"high": "31", "medium": "33", "low": "32"}  # ANSI red / yellow / green

# (keywords, emoji): the first row whose keyword appears in the description wins
TASK_ICONS = [
    (("walk",), "🦮"),
    (("feed", "breakfast", "dinner", "lunch", "meal"), "🍖"),
    (("med", "pill"), "💊"),
    (("vet",), "🩺"),
    (("groom", "brush", "bath"), "🛁"),
    (("play", "fetch"), "🎾"),
    (("clean", "litter", "cage"), "🧹"),
    (("water",), "💧"),
]


def task_icon(description: str) -> str:
    """Emoji for the kind of task, guessed from its description (paw print if unknown)."""
    text = description.lower()
    for keywords, icon in TASK_ICONS:
        if any(word in text for word in keywords):
            return icon
    return "🐾"


def color(text: str, code: str) -> str:
    """Wrap text in an ANSI color code."""
    return f"\033[{code}m{text}\033[0m"


def priority_label(priority: str) -> str:
    """Color-coded priority, for example a red "🔴 high"."""
    return color(f"{PRIORITY_ICON[priority]} {priority}", PRIORITY_COLOR[priority])


def status_label(completed: bool) -> str:
    """Green check for done tasks, yellow circle for tasks still to do."""
    return color("✔ done", "32") if completed else color("○ to do", "33")


def _table(rows: list, headers: list) -> str:
    if tabulate is None:
        raise ImportError("Pretty output needs tabulate: pip install -r requirements.txt")
    return tabulate(rows, headers=headers, tablefmt="rounded_grid")


def format_tasks(tasks: List) -> str:
    """Table of tasks with task-type emoji and color-coded priority and status."""
    rows = [
        [
            f"{task_icon(t.description)} {t.description}",
            t.pet_name,
            t.time or "-",
            t.duration_minutes,
            priority_label(t.priority),
            status_label(t.completed),
        ]
        for t in tasks
    ]
    return _table(rows, ["Task", "Pet", "Time", "Min", "Priority", "Status"])


def format_schedule(owner, plan) -> str:
    """Table of the day's plan, followed by time used and anything skipped."""
    rows = [
        [
            f"{item.start_minute}-{item.end_minute}",
            f"{task_icon(item.task.description)} {item.task.description}",
            item.task.pet_name,
            priority_label(item.task.priority),
            item.task.duration_minutes,
        ]
        for item in plan.scheduled
    ]
    lines = [
        f"Today's Schedule for {owner.name}",
        _table(rows, ["Minutes", "Task", "Pet", "Priority", "Duration"]),
        color(f"Total: {plan.total_minutes}/{owner.available_minutes} min", "36"),
    ]
    for task, reason in plan.skipped:
        lines.append(color(f"Skipped {task.description} ({task.pet_name}): {reason}", "33"))
    return "\n".join(lines)
