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



def main() -> None:
    owner = Owner(name="Jason", available_minutes=90)

    biscuit = Pet(name="Biscuit", species="dog")
    luna = Pet(name="Luna", species="cat")
    kiwi = Pet(name="Kiwi", species="bird")
    for pet in (biscuit, luna, kiwi):
        owner.add_pet(pet)

    biscuit.add_task(Task("Morning walk", 30, priority="high", time="07:30", frequency="daily"))
    luna.add_task(Task("Breakfast", 10, priority="high", time="08:00", frequency="daily"))
    kiwi.add_task(Task("Clean cage", 25, priority="medium", time="12:00", frequency="weekly"))
    biscuit.add_task(Task("Evening play", 20, priority="low", time="18:30", frequency="daily"))

    scheduler = Scheduler(owner)
    print_schedule(owner, scheduler.generate_plan())


if __name__ == "__main__":
    main()
