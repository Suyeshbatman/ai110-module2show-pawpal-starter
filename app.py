import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.markdown("A smart pet care planning assistant that helps you organize daily tasks for your pets.")

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Sidebar — Owner info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Owner Info")
    new_name = st.text_input("Your name", value=owner.name)
    if new_name != owner.name:
        owner.name = new_name

    st.divider()
    st.header("Add a Pet")
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    pet_age = st.number_input("Age", min_value=0, max_value=30, value=2)

    if st.button("Add pet"):
        if owner.get_pet_by_name(pet_name):
            st.warning(f"A pet named '{pet_name}' already exists.")
        else:
            owner.add_pet(Pet(name=pet_name, species=species, age=pet_age))
            st.success(f"Added {pet_name}!")

    if owner.pets:
        st.divider()
        st.subheader("Your Pets")
        for pet in owner.pets:
            st.write(f"**{pet.name}** — {pet.species}, age {pet.age}")

# ---------------------------------------------------------------------------
# Main area — Task management
# ---------------------------------------------------------------------------
if not owner.pets:
    st.info("Add a pet in the sidebar to get started.")
    st.stop()

st.subheader("Add a Task")

pet_names = [p.name for p in owner.pets]
col1, col2 = st.columns(2)
with col1:
    selected_pet = st.selectbox("Pet", pet_names)
with col2:
    task_desc = st.text_input("Task description", value="Morning walk")

col3, col4, col5, col6 = st.columns(4)
with col3:
    task_time = st.text_input("Time (HH:MM)", value="08:00")
with col4:
    task_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=30)
with col5:
    task_priority = st.selectbox("Priority", ["high", "medium", "low"])
with col6:
    task_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

if st.button("Add task"):
    # Validate time format
    try:
        parts = task_time.split(":")
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
    except (ValueError, IndexError):
        st.error("Please enter time in HH:MM format (e.g. 08:00).")
    else:
        pet = owner.get_pet_by_name(selected_pet)
        if pet:
            pet.add_task(Task(
                description=task_desc,
                time=task_time,
                duration_minutes=int(task_duration),
                priority=task_priority,
                frequency=task_frequency,
            ))
            st.success(f"Added '{task_desc}' for {selected_pet}.")

# ---------------------------------------------------------------------------
# Current tasks display
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Current Tasks")

scheduler = Scheduler(owner)
all_tasks = scheduler.get_all_tasks()

if not all_tasks:
    st.info("No tasks yet. Add one above.")
else:
    # Filter controls
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names, key="filter_pet")
    with filter_col2:
        filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"], key="filter_status")

    display_tasks = all_tasks
    if filter_pet != "All":
        display_tasks = scheduler.filter_by_pet(filter_pet)
    if filter_status == "Pending":
        display_tasks = [t for t in display_tasks if not t.completed]
    elif filter_status == "Completed":
        display_tasks = [t for t in display_tasks if t.completed]

    if display_tasks:
        task_data = []
        for t in scheduler.sort_by_time(display_tasks):
            task_data.append({
                "Time": t.time,
                "Task": t.description,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority.capitalize(),
                "Frequency": t.frequency.capitalize(),
                "Status": "Done" if t.completed else "Pending",
            })
        st.table(task_data)
    else:
        st.info("No tasks match the current filter.")

# ---------------------------------------------------------------------------
# Schedule generation
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Generate Daily Schedule")

if st.button("Generate schedule"):
    pending = scheduler.filter_by_status(completed=False)
    if not pending:
        st.warning("No pending tasks to schedule.")
    else:
        summary = scheduler.get_schedule_summary()

        # Conflict warnings
        if summary["conflicts"]:
            for warning in summary["conflicts"]:
                st.warning(f"⚠️ {warning}")

        # Schedule table
        st.markdown(f"**{summary['total_tasks']} tasks** — {summary['total_minutes']} minutes total")

        schedule_data = []
        for entry in summary["explanations"]:
            t = entry["task"]
            schedule_data.append({
                "Time": f"{t.time} - {t.end_time_str()}",
                "Task": t.description,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority.capitalize(),
            })
        st.table(schedule_data)

        # Reasoning
        with st.expander("View scheduling reasoning"):
            for entry in summary["explanations"]:
                st.write(entry["reason"])

# ---------------------------------------------------------------------------
# Mark tasks complete
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Mark Task Complete")

pending_tasks = scheduler.filter_by_status(completed=False)
if pending_tasks:
    task_options = [f"{t.description} ({t.time})" for t in pending_tasks]
    selected_task_label = st.selectbox("Select task to complete", task_options)
    idx = task_options.index(selected_task_label)

    if st.button("Mark complete"):
        task_to_complete = pending_tasks[idx]
        new_task = scheduler.mark_task_complete(task_to_complete)
        st.success(f"'{task_to_complete.description}' marked as complete!")
        if new_task:
            st.info(f"Next occurrence created for {new_task.due_date} ({new_task.frequency}).")
        st.rerun()
else:
    st.info("No pending tasks to complete.")
