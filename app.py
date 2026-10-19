from datetime import datetime

import streamlit as st

from diagrams.pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks for the day based on time and priority.")

# Streamlit reruns this whole script on every interaction, so the Owner lives in
# st.session_state (a per-session dict kept in server memory). It's only created
# when the key is missing, so pets and tasks survive reruns.
if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(name="Jordan", available_minutes=90)
owner: Owner = st.session_state["owner"]
# Seed the time dropdowns once from the owner's value (they keep their own state after).
st.session_state.setdefault("hours", owner.available_minutes // 60)
st.session_state.setdefault("minutes", owner.available_minutes % 60)

if st.button("Start over"):
    for key in ("owner", "hours", "minutes"):
        st.session_state.pop(key, None)  # delete the stored Owner and its time inputs...
    st.rerun()  # ...and rerun so a fresh one is created above

# --- Owner -----------------------------------------------------------------
st.subheader("Owner")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    owner.name = st.text_input("Owner name", value=owner.name)
with col2:
    hours = st.selectbox("Time available: hours", list(range(0, 8)), key="hours")  # max 7h55m
with col3:
    minutes = st.selectbox("minutes", list(range(0, 60, 5)), key="minutes")

if hours * 60 + minutes == 0:
    st.warning("Choose at least 5 minutes of available time.")
else:
    owner.available_minutes = hours * 60 + minutes

# --- Pets ------------------------------------------------------------------
st.subheader("Pets")
col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "bird", "other"])

if st.button("Add pet"):
    name = pet_name.strip()
    if not name:
        st.error("Pet name can't be empty.")
    elif any(p.name.lower() == name.lower() for p in owner.pets):
        st.error(f"You already have a pet named {name}.")
    else:
        owner.add_pet(Pet(name=name, species=species))

if owner.pets:
    st.table([{"Name": p.name, "Species": p.species, "Tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

# --- Tasks -----------------------------------------------------------------
st.subheader("Tasks")

if owner.pets:
    pet_choice = st.selectbox("Task for", [p.name for p in owner.pets])
    col1, col2 = st.columns(2)
    with col1:
        description = st.text_input("Task description", value="Morning walk")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col2:
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=1)
        preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")

    if st.button("Add task"):
        time_value = preferred_time.strip() or None
        try:
            if not description.strip():
                raise ValueError("Task description can't be empty.")
            if time_value:
                datetime.strptime(time_value, "%H:%M")
            task = Task(
                description=description.strip(),
                duration_minutes=int(duration),
                priority=priority,
                time=time_value,
                frequency=frequency,
            )
        except ValueError as err:
            st.error(f"Couldn't add task: {err}")
        else:
            next(p for p in owner.pets if p.name == pet_choice).add_task(task)
else:
    st.info("Add a pet before adding tasks.")

scheduler = Scheduler(owner)
all_tasks = owner.get_all_tasks()

if flash := st.session_state.pop("flash", None):
    st.success(flash)

if all_tasks:
    # Conflicts: shown right next to the tasks so the owner sees them as soon as they happen.
    conflicts = scheduler.detect_conflicts()
    for conflict in conflicts:
        st.warning(f"⚠️ {conflict}. You can't do both at once, so change one task's preferred time.")
    if not conflicts:
        st.success("No time conflicts between your tasks.")

    # Mark a task done (recurring tasks automatically get their next occurrence).
    pending = scheduler.get_pending_tasks()
    if pending:
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            choice = st.selectbox(
                "Mark a task complete",
                range(len(pending)),
                format_func=lambda i: f"{pending[i].description} ({pending[i].pet_name}, due {pending[i].due_date})",
            )
        with col2:
            if st.button("Mark complete"):
                task = pending[choice]
                next_task = scheduler.mark_task_complete(task)
                message = f"Marked '{task.description}' ({task.pet_name}) complete."
                if next_task:
                    message += f" Next {task.frequency} task created for {next_task.due_date}."
                st.session_state["flash"] = message
                st.rerun()  # redraw so the table below shows the change

    # View controls: filter with Scheduler.filter_tasks, order with sort_by_time / sort_tasks.
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets], key="filter_pet")
    with col2:
        status_filter = st.selectbox("Show status", ["All", "Pending", "Completed"], key="filter_status")
    with col3:
        sort_choice = st.selectbox("Sort by", ["Time", "Priority", "Order added"], key="sort_by")

    visible = scheduler.filter_tasks(
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
        pet_name=None if pet_filter == "All pets" else pet_filter,
    )
    if sort_choice == "Time":
        visible = scheduler.sort_by_time(visible)
    elif sort_choice == "Priority":
        visible = scheduler.sort_tasks(visible)

    if visible:
        st.table(
            [
                {
                    "Pet": t.pet_name,
                    "Task": t.description,
                    "Time": t.time or "-",
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Repeats": t.frequency,
                    "Due": t.due_date.isoformat(),
                    "Status": "✅ Done" if t.completed else "⏳ To do",
                }
                for t in visible
            ]
        )
    else:
        st.info("No tasks match these filters.")
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule --------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    plan = scheduler.generate_plan()

    if plan.scheduled:
        st.success(
            f"Scheduled {len(plan.scheduled)} task(s): "
            f"{plan.total_minutes} of {owner.available_minutes} minutes used."
        )
        st.table(
            [
                {
                    "Minutes": f"{item.start_minute}-{item.end_minute}",
                    "Pet": item.task.pet_name,
                    "Task": item.task.description,
                    "Priority": item.task.priority,
                    "Duration": item.task.duration_minutes,
                }
                for item in plan.scheduled
            ]
        )
    else:
        st.info("Nothing to schedule right now: no pending tasks are due today.")

    for task, reason in plan.skipped:
        st.warning(f"Skipped {task.description} ({task.pet_name}): {reason}")

    with st.expander("Why this plan?"):
        st.text(scheduler.explain_plan())
