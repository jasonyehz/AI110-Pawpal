from pawpal_system import Owner, Pet, Plan, Scheduler, Task


def print_schedule(owner: Owner, plan: Plan) -> None:
    print(f"Today's Schedule for {owner.name}")
    print("-" * 40)
    for item in plan.scheduled:
        t = item.task
        print(
            f"{item.start_minute}-{item.end_minute} min: {t.description} "
            f"({t.pet_name}, {t.priority}, {t.duration_minutes} min)"
        )
    print("-" * 40)
    print(f"Total: {plan.total_minutes}/{owner.available_minutes} min")

    if plan.skipped:
        print("Skipped:")
        for task, reason in plan.skipped:
            print(f"- {task.description} ({task.pet_name}): {reason}")



def print_tasks(title: str, tasks: list) -> None:
    print(title)
    for t in tasks:
        status = "done" if t.completed else "todo"
        print(f"  {t.time or '--:--':<5}  {t.description} ({t.pet_name}, {status})")
    print()


def main() -> None:
    owner = Owner(name="Jason", available_minutes=90)

    biscuit = Pet(name="Biscuit", species="dog")
    luna = Pet(name="Luna", species="cat")
    kiwi = Pet(name="Kiwi", species="bird")
    for pet in (biscuit, luna, kiwi):
        owner.add_pet(pet)

    # Added deliberately out of time order
    biscuit.add_task(Task("Evening play", 20, priority="low", time="18:30", frequency="daily"))
    kiwi.add_task(Task("Clean cage", 25, priority="medium", time="12:00", frequency="weekly"))
    luna.add_task(Task("Breakfast", 10, priority="high", time="08:00", frequency="daily"))
    biscuit.add_task(Task("Morning walk", 30, priority="high", time="07:30", frequency="daily"))
    luna.add_task(Task("Brush fur", 5, priority="low"))  # no preferred time
    # Deliberate clashes: Vet call vs Clean cage (different pets), meds vs playtime (same pet)
    biscuit.add_task(Task("Vet call", 15, priority="medium", time="12:00"))
    luna.add_task(Task("Give meds", 5, priority="high", time="19:00", frequency="daily"))
    luna.add_task(Task("Playtime", 15, priority="low", time="19:00"))

    luna.tasks[0].mark_complete()  # Breakfast is already done

    scheduler = Scheduler(owner)

    print_tasks("All tasks, in the order added:", owner.get_all_tasks())
    print_tasks("Sorted by time:", scheduler.sort_by_time())
    print_tasks("Only Biscuit's tasks:", scheduler.filter_tasks(pet_name="Biscuit"))
    print_tasks("Completed tasks:", scheduler.filter_tasks(completed=True))
    print_tasks("Pending tasks:", scheduler.filter_tasks(completed=False))
    print_tasks(
        "Luna's pending tasks, sorted by time:",
        scheduler.sort_by_time(scheduler.filter_tasks(completed=False, pet_name="Luna")),
    )

    print("Conflict check:")
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts or ["No conflicts."]:
        print(f"  WARNING: {warning}" if conflicts else f"  {warning}")
    print()

    print("Completing a daily and a weekly task creates the next occurrence:")
    walk = next(t for t in biscuit.tasks if t.description == "Morning walk")
    cage = kiwi.tasks[0]
    for task in (walk, cage):
        nxt = scheduler.mark_task_complete(task)
        print(f"  {task.description} ({task.frequency}, due {task.due_date}) -> next due {nxt.due_date}")
    print(f"  Biscuit now has {len(biscuit.tasks)} tasks, Kiwi has {len(kiwi.tasks)}")

    print()
    print_schedule(owner, scheduler.generate_plan())


if __name__ == "__main__":
    main()
