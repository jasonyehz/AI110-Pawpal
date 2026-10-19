import sys
from datetime import date, timedelta
from pathlib import Path

# pawpal_system.py currently lives in diagrams/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "diagrams"))

from pawpal_system import Owner, Pet, Scheduler, Task


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


def test_sort_by_time_orders_earliest_first_and_untimed_last():
    owner = Owner(name="Jason", available_minutes=120)
    pet = Pet(name="Biscuit", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Evening play", 20, time="18:30"))
    pet.add_task(Task("No time", 5))
    pet.add_task(Task("Early walk", 30, time="9:05"))  # unpadded: a plain string sort gets this wrong
    pet.add_task(Task("Lunch", 10, time="12:00"))

    ordered = Scheduler(owner).sort_by_time()

    assert [t.description for t in ordered] == ["Early walk", "Lunch", "Evening play", "No time"]


def test_filter_tasks_by_completion_and_pet_name():
    owner = Owner(name="Jason", available_minutes=120)
    biscuit, luna = Pet("Biscuit", "dog"), Pet("Luna", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(luna)
    walk, play, feed = Task("Walk", 30), Task("Play", 20), Task("Feed", 10)
    biscuit.add_task(walk)
    biscuit.add_task(play)
    luna.add_task(feed)
    walk.mark_complete()

    scheduler = Scheduler(owner)

    assert scheduler.filter_tasks(completed=True) == [walk]
    assert scheduler.filter_tasks(completed=False) == [play, feed]
    assert scheduler.filter_tasks(pet_name="Luna") == [feed]
    assert scheduler.filter_tasks(completed=False, pet_name="Biscuit") == [play]
    assert len(scheduler.filter_tasks()) == 3


def _owner_with_task(task):
    owner = Owner(name="Jason", available_minutes=120)
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    pet.add_task(task)
    return owner, pet


def test_completing_daily_task_creates_next_day_occurrence():
    task = Task("Walk", 30, frequency="daily")
    owner, pet = _owner_with_task(task)

    new_task = Scheduler(owner).mark_task_complete(task)

    assert task.completed is True
    assert new_task is not task and new_task.completed is False
    assert new_task.due_date == task.due_date + timedelta(days=1)
    assert new_task.pet_name == "Biscuit"
    assert pet.tasks == [task, new_task]


def test_completing_weekly_task_creates_occurrence_seven_days_later():
    task = Task("Clean cage", 25, frequency="weekly")
    owner, _ = _owner_with_task(task)

    new_task = Scheduler(owner).mark_task_complete(task)

    assert new_task.due_date == task.due_date + timedelta(days=7)


def test_completing_one_time_task_creates_nothing_and_no_duplicates():
    once = Task("Vet visit", 60, frequency="once")
    daily = Task("Walk", 30, frequency="daily")
    owner, pet = _owner_with_task(once)
    pet.add_task(daily)
    scheduler = Scheduler(owner)

    assert scheduler.mark_task_complete(once) is None
    assert len(pet.tasks) == 2

    scheduler.mark_task_complete(daily)
    assert scheduler.mark_task_complete(daily) is None  # already complete
    assert len(pet.tasks) == 3


def test_plan_only_includes_tasks_due_today():
    task = Task("Walk", 30, frequency="daily")
    owner, _ = _owner_with_task(task)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(task)  # next one is due tomorrow

    plan = scheduler.generate_plan()

    assert plan.scheduled == []
    assert scheduler.get_due_tasks(on=date.today() + timedelta(days=1))[0].due_date == (
        date.today() + timedelta(days=1)
    )


def test_detect_conflicts_flags_same_time_for_same_and_different_pets():
    owner = Owner(name="Jason", available_minutes=120)
    biscuit, luna = Pet("Biscuit", "dog"), Pet("Luna", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(luna)
    biscuit.add_task(Task("Walk", 30, time="08:00"))
    luna.add_task(Task("Feed", 10, time="8:00"))  # same time, unpadded, different pet
    luna.add_task(Task("Meds", 5, time="19:00"))
    luna.add_task(Task("Play", 15, time="19:00"))  # same time, same pet
    luna.add_task(Task("Brush", 5, time="21:00"))  # no clash
    luna.add_task(Task("Nap check", 5))  # no time, never a clash

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 2
    assert "across pets" in warnings[0] and "08:00" in warnings[0]
    assert "for Luna" in warnings[1] and "19:00" in warnings[1]


def test_detect_conflicts_ignores_completed_tasks_and_returns_empty_list_when_clear():
    owner = Owner(name="Jason", available_minutes=120)
    pet = Pet("Biscuit", "dog")
    owner.add_pet(pet)
    done, todo = Task("Walk", 30, time="08:00"), Task("Feed", 10, time="08:00")
    pet.add_task(done)
    pet.add_task(todo)
    done.mark_complete()

    assert Scheduler(owner).detect_conflicts() == []
