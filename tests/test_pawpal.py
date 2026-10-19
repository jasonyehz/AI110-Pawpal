import sys
from datetime import date, timedelta
from pathlib import Path

# pawpal_system.py currently lives in diagrams/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "diagrams"))

import pytest

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


# --- helpers ---------------------------------------------------------------


def make_scheduler(available_minutes=120, **pets):
    """Owner with the given pets (name=[tasks]) and a Scheduler for them."""
    owner = Owner(name="Jason", available_minutes=available_minutes)
    for name, tasks in pets.items():
        pet = Pet(name, "dog")
        owner.add_pet(pet)
        for task in tasks:
            pet.add_task(task)
    return Scheduler(owner)


# --- sorting ---------------------------------------------------------------


def test_sort_by_time_with_no_tasks_returns_empty_list():
    assert make_scheduler(Biscuit=[]).sort_by_time() == []


def test_sort_by_time_keeps_original_order_for_equal_times():
    first, second = Task("First", 10, time="08:00"), Task("Second", 10, time="08:00")

    ordered = make_scheduler(Biscuit=[first, second]).sort_by_time()

    assert ordered == [first, second]


def test_sort_tasks_orders_by_priority_then_time_then_duration():
    low_early = Task("Low early", 10, priority="low", time="06:00")
    high_late = Task("High late", 10, priority="high", time="20:00")
    high_early_long = Task("High early long", 30, priority="high", time="07:00")
    high_early_short = Task("High early short", 5, priority="high", time="07:00")
    high_untimed = Task("High untimed", 5, priority="high")
    tasks = [low_early, high_late, high_early_long, high_untimed, high_early_short]

    ordered = make_scheduler(Biscuit=tasks).sort_tasks(tasks)

    assert ordered == [high_early_short, high_early_long, high_late, high_untimed, low_early]


# --- filtering -------------------------------------------------------------


def test_filter_tasks_unknown_pet_or_pet_without_tasks_returns_empty_list():
    scheduler = make_scheduler(Biscuit=[Task("Walk", 30)], Luna=[])

    assert scheduler.filter_tasks(pet_name="Nobody") == []
    assert scheduler.filter_tasks(pet_name="Luna") == []


def test_filter_tasks_pet_name_is_case_insensitive():
    walk = Task("Walk", 30)
    scheduler = make_scheduler(Biscuit=[walk])

    assert scheduler.filter_tasks(pet_name="bIsCuIt") == [walk]


# --- recurring tasks -------------------------------------------------------


# Dates are far in the future so these stay valid as time passes (next_occurrence
# never schedules before today).
@pytest.mark.parametrize(
    "frequency, start, expected",
    [
        ("daily", date(2030, 10, 31), date(2030, 11, 1)),  # month rollover
        ("daily", date(2030, 12, 31), date(2031, 1, 1)),  # year rollover
        ("daily", date(2032, 2, 28), date(2032, 2, 29)),  # leap day exists in 2032
        ("daily", date(2031, 2, 28), date(2031, 3, 1)),  # ...but not in 2031
        ("weekly", date(2030, 12, 28), date(2031, 1, 4)),  # weekly across the new year
    ],
)
def test_next_occurrence_handles_calendar_rollovers(frequency, start, expected):
    task = Task("Walk", 30, frequency=frequency, due_date=start)

    assert task.next_occurrence().due_date == expected


def test_next_occurrence_copies_details_but_resets_completion():
    task = Task("Meds", 5, priority="high", time="08:00", frequency="daily", pet_name="Luna")
    task.mark_complete()

    new_task = task.next_occurrence()

    assert new_task is not task
    assert (new_task.description, new_task.duration_minutes, new_task.priority) == ("Meds", 5, "high")
    assert (new_task.time, new_task.frequency, new_task.pet_name) == ("08:00", "daily", "Luna")
    assert new_task.completed is False


def test_mark_task_complete_for_task_not_owned_raises_value_error():
    scheduler = make_scheduler(Biscuit=[Task("Walk", 30)])

    with pytest.raises(ValueError):
        scheduler.mark_task_complete(Task("Stranger", 10, frequency="daily"))


def test_overdue_task_still_appears_in_todays_plan():
    overdue = Task("Meds", 5, due_date=date.today() - timedelta(days=2))
    scheduler = make_scheduler(Biscuit=[overdue])

    assert [item.task for item in scheduler.generate_plan().scheduled] == [overdue]


# --- conflicts -------------------------------------------------------------


def test_same_time_on_different_dates_is_not_a_conflict():
    today, tomorrow = date.today(), date.today() + timedelta(days=1)
    scheduler = make_scheduler(
        Biscuit=[Task("Walk", 30, time="08:00", due_date=today),
                 Task("Walk", 30, time="08:00", due_date=tomorrow)]
    )

    assert scheduler.detect_conflicts() == []


def test_three_tasks_at_one_time_produce_a_single_warning():
    tasks = [Task(name, 5, time="08:00") for name in ("A", "B", "C")]

    warnings = make_scheduler(Biscuit=tasks).detect_conflicts()

    assert len(warnings) == 1
    assert "3 tasks" in warnings[0]


# --- plan generation -------------------------------------------------------


def test_plan_places_tasks_back_to_back_from_minute_zero():
    walk, feed = Task("Walk", 30, priority="high"), Task("Feed", 10, priority="medium")

    plan = make_scheduler(Biscuit=[feed, walk]).generate_plan()

    assert [(i.task, i.start_minute, i.end_minute) for i in plan.scheduled] == [
        (walk, 0, 30),
        (feed, 30, 40),
    ]
    assert plan.skipped == []
    assert plan.total_minutes == 40


def test_task_that_exactly_fills_remaining_time_is_scheduled():
    plan = make_scheduler(available_minutes=30, Biscuit=[Task("Walk", 30)]).generate_plan()

    assert len(plan.scheduled) == 1 and plan.skipped == []


def test_oversized_task_is_skipped_but_later_smaller_task_still_fits():
    big = Task("Big", 50, priority="high")
    small = Task("Small", 10, priority="low")

    plan = make_scheduler(available_minutes=30, Biscuit=[big, small]).generate_plan()

    assert [i.task for i in plan.scheduled] == [small]
    assert plan.skipped[0][0] is big and "50 min" in plan.skipped[0][1]


def test_plan_is_empty_with_no_pets_no_tasks_or_all_tasks_completed():
    done = Task("Walk", 30)
    done.mark_complete()

    assert make_scheduler().generate_plan().scheduled == []
    assert make_scheduler(Biscuit=[]).generate_plan().scheduled == []
    assert make_scheduler(Biscuit=[done]).generate_plan().scheduled == []


def test_zero_available_minutes_skips_every_task():
    plan = make_scheduler(available_minutes=0, Biscuit=[Task("Walk", 30)]).generate_plan()

    assert plan.scheduled == [] and len(plan.skipped) == 1


def test_explain_plan_generates_a_plan_when_none_exists_yet():
    scheduler = make_scheduler(Biscuit=[Task("Walk", 30)])
    assert scheduler.plan is None

    text = scheduler.explain_plan()

    assert scheduler.plan is not None
    assert "Walk" in text


# --- validation ------------------------------------------------------------


@pytest.mark.parametrize("duration", [0, -5])
def test_task_rejects_non_positive_duration(duration):
    with pytest.raises(ValueError):
        Task("Walk", duration)


def test_task_rejects_unknown_priority_and_frequency():
    with pytest.raises(ValueError):
        Task("Walk", 10, priority="urgent")
    with pytest.raises(ValueError):
        Task("Walk", 10, frequency="monthly")


def test_task_normalizes_priority_and_frequency_case():
    task = Task("Walk", 10, priority="HIGH", frequency="Daily")

    assert (task.priority, task.frequency) == ("high", "daily")


@pytest.mark.parametrize("bad_time", ["abc", "25:99", "8", "08:60"])
def test_task_rejects_malformed_preferred_time(bad_time):
    with pytest.raises(ValueError):
        Task("Walk", 10, time=bad_time)


# --- regressions found by fuzzing -------------------------------------------


def test_completing_overdue_daily_task_schedules_next_one_for_tomorrow():
    overdue = Task("Meds", 5, frequency="daily", due_date=date.today() - timedelta(days=3))
    scheduler = make_scheduler(Biscuit=[overdue])

    new_task = scheduler.mark_task_complete(overdue)

    assert new_task.due_date == date.today() + timedelta(days=1)
    assert scheduler.generate_plan().scheduled == []  # nothing left to do today


def test_completing_a_task_early_keeps_the_original_schedule():
    due_in_5_days = date.today() + timedelta(days=5)
    task = Task("Bath", 30, frequency="weekly", due_date=due_in_5_days)

    assert task.next_occurrence().due_date == due_in_5_days + timedelta(days=7)


def test_explain_plan_reflects_tasks_added_after_generate_plan():
    scheduler = make_scheduler(Biscuit=[Task("Walk", 10)])
    scheduler.generate_plan()
    scheduler.owner.pets[0].add_task(Task("Feed", 10))

    assert "Feed" in scheduler.explain_plan()


def test_remove_task_removes_the_exact_task_not_an_equal_one():
    pet = Pet("Biscuit", "dog")
    first, second = Task("Walk", 5), Task("Walk", 5)  # equal by value
    pet.add_task(first)
    pet.add_task(second)

    pet.remove_task(second)

    assert len(pet.tasks) == 1 and pet.tasks[0] is first


def test_remove_task_not_on_pet_raises_value_error():
    with pytest.raises(ValueError):
        Pet("Biscuit", "dog").remove_task(Task("Walk", 5))


def test_owner_rejects_negative_available_minutes():
    with pytest.raises(ValueError):
        Owner(name="Jason", available_minutes=-5)


@pytest.mark.parametrize("description", ["", "   "])
def test_task_rejects_empty_description(description):
    with pytest.raises(ValueError):
        Task(description, 10)
