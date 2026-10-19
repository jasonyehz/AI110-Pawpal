import json
import sys
from datetime import date, timedelta
from pathlib import Path

# pawpal_system.py currently lives in diagrams/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "diagrams"))

import pytest

import formatting
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


# --- weekly recurrence keeps the weekday -----------------------------------

MONDAY = date(2026, 10, 12)


@pytest.mark.parametrize(
    "today, expected",
    [
        (date(2026, 10, 12), date(2026, 10, 19)),  # done on time -> next Monday
        (date(2026, 10, 22), date(2026, 10, 26)),  # done late on a Thursday -> still a Monday
        (date(2026, 10, 19), date(2026, 10, 26)),  # done exactly a week late -> strictly after today
        (date(2026, 10, 1), date(2026, 10, 19)),  # done early -> at least 7 days after the old due date
    ],
)
def test_weekly_task_keeps_its_weekday(today, expected):
    task = Task("Clean cage", 25, frequency="weekly", due_date=MONDAY)

    new_due = task.next_occurrence(today=today).due_date

    assert new_due == expected
    assert new_due.weekday() == MONDAY.weekday()


def test_next_occurrence_with_explicit_today_for_daily_and_once():
    assert Task("Walk", 30, frequency="daily", due_date=MONDAY).next_occurrence(today=date(2026, 10, 20)).due_date == date(2026, 10, 21)
    assert Task("Vet", 30, frequency="once").next_occurrence(today=MONDAY) is None


# --- next available slot ---------------------------------------------------


def slot_scheduler(*timed):
    """Scheduler whose only tasks are (time, minutes) blocks due today."""
    return make_scheduler(Biscuit=[Task(f"T{i}", minutes, time=at) for i, (at, minutes) in enumerate(timed)])


def test_free_day_returns_the_start_of_the_day():
    assert slot_scheduler().find_next_available_slot(30) == "06:00"


def test_slot_skips_past_a_busy_block_using_its_duration():
    scheduler = slot_scheduler(("06:00", 90))  # busy until 07:30

    assert scheduler.find_next_available_slot(30) == "07:30"


def test_slot_uses_a_gap_between_tasks_when_it_fits_and_skips_it_when_it_does_not():
    scheduler = slot_scheduler(("06:00", 60), ("08:00", 60))  # gap 07:00-08:00

    assert scheduler.find_next_available_slot(60) == "07:00"
    assert scheduler.find_next_available_slot(61) == "09:00"


def test_slot_handles_overlapping_busy_blocks():
    scheduler = slot_scheduler(("06:00", 120), ("07:00", 30), ("07:30", 90))  # all busy until 09:00

    assert scheduler.find_next_available_slot(15) == "09:00"


def test_slot_respects_after_and_returns_none_when_the_day_is_full():
    scheduler = slot_scheduler(("06:00", 60))

    assert scheduler.find_next_available_slot(30, after="12:00") == "12:00"
    assert scheduler.find_next_available_slot(30, after="21:45") is None  # would run past 22:00
    assert scheduler.find_next_available_slot(16 * 60) is None  # longer than the whole day window
    assert scheduler.find_next_available_slot(30, after="22:00") is None


def test_slot_ignores_completed_untimed_and_other_day_tasks():
    done = Task("Done", 600, time="06:00")
    done.mark_complete()
    untimed = Task("Untimed", 600)
    tomorrow = Task("Tomorrow", 600, time="06:00", due_date=date.today() + timedelta(days=1))
    scheduler = make_scheduler(Biscuit=[done, untimed, tomorrow])

    assert scheduler.find_next_available_slot(30) == "06:00"


def test_slot_rejects_non_positive_duration():
    with pytest.raises(ValueError):
        slot_scheduler().find_next_available_slot(0)


# --- saving and loading ----------------------------------------------------


def sample_owner():
    owner = Owner(name="Jason", available_minutes=95)
    biscuit, luna = Pet("Biscuit", "dog"), Pet("Luna", "cat")
    owner.add_pet(biscuit)
    owner.add_pet(luna)
    biscuit.add_task(Task("Walk", 30, priority="high", time="07:30", frequency="daily"))
    done = Task("Feed", 10, due_date=date(2026, 3, 1))
    done.mark_complete()
    luna.add_task(done)
    return owner


def test_save_and_load_round_trips_everything(tmp_path):
    owner = sample_owner()
    path = tmp_path / "data.json"

    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded == owner
    walk = loaded.pets[0].tasks[0]
    assert (walk.pet_name, walk.time, walk.frequency, walk.due_date) == ("Biscuit", "07:30", "daily", date.today())
    assert loaded.pets[1].tasks[0].completed is True
    assert loaded.pets[1].tasks[0].due_date == date(2026, 3, 1)


def test_saved_file_is_readable_json_with_iso_dates_and_no_temp_file_left(tmp_path):
    path = tmp_path / "data.json"

    sample_owner().save_to_json(path)

    data = json.loads(path.read_text())
    assert data["pets"][1]["tasks"][0]["due_date"] == "2026-03-01"
    assert list(tmp_path.iterdir()) == [path]


def test_saving_again_overwrites_the_old_data(tmp_path):
    path = tmp_path / "data.json"
    sample_owner().save_to_json(path)

    Owner(name="Empty", available_minutes=10).save_to_json(path)

    loaded = Owner.load_from_json(path)
    assert (loaded.name, loaded.pets) == ("Empty", [])


def test_loaded_tasks_work_with_the_scheduler(tmp_path):
    path = tmp_path / "data.json"
    sample_owner().save_to_json(path)

    scheduler = Scheduler(Owner.load_from_json(path))

    assert [i.task.description for i in scheduler.generate_plan().scheduled] == ["Walk"]


def test_load_from_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(tmp_path / "nope.json")


@pytest.mark.parametrize(
    "content",
    [
        "{ not json",
        "[]",
        '{"name": "Jason"}',  # missing fields
        '{"name": "J", "available_minutes": 5, "pets": [{"name": "P", "species": "dog", "tasks": '
        '[{"description": "x", "duration_minutes": 5, "priority": "urgent", "time": null, '
        '"frequency": "once", "completed": false, "pet_name": "P", "due_date": "2026-01-01"}]}]}',  # bad priority
    ],
)
def test_load_from_bad_file_raises_value_error(tmp_path, content):
    path = tmp_path / "data.json"
    path.write_text(content)

    with pytest.raises(ValueError):
        Owner.load_from_json(path)


# --- formatting ------------------------------------------------------------


def test_task_icon_matches_keywords_case_insensitively_with_a_default():
    assert formatting.task_icon("Morning WALK") == "🦮"
    assert formatting.task_icon("Give meds") == "💊"
    assert formatting.task_icon("Something else") == "🐾"


def test_priority_and_status_labels_are_color_coded():
    assert "\033[31m" in formatting.priority_label("high")  # red
    assert "\033[32m" in formatting.priority_label("low")  # green
    assert "done" in formatting.status_label(True) and "to do" in formatting.status_label(False)


def test_pretty_tables_contain_every_task():
    pytest.importorskip("tabulate")
    scheduler = Scheduler(sample_owner().__class__.from_dict(sample_owner().to_dict()))
    owner = scheduler.owner

    table = formatting.format_tasks(owner.get_all_tasks())
    schedule = formatting.format_schedule(owner, scheduler.generate_plan())

    assert "Walk" in table and "Feed" in table
    assert "Walk" in schedule and "Total: 30/95 min" in schedule
