import sys
from pathlib import Path

# pawpal_system.py currently lives in diagrams/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "diagrams"))

from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Biscuit", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Morning walk", 30))
    assert len(pet.tasks) == 1

    pet.add_task(Task("Evening play", 20))
    assert len(pet.tasks) == 2
