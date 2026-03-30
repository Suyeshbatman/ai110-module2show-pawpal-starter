"""Demo script - verifies PawPal+ logic in the terminal."""

from pawpal_system import Task, Pet, Owner, Scheduler


def main():
    # --- Create owner and pets -----------------------------------------------
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog", age=3)
    whiskers = Pet(name="Whiskers", species="cat", age=5)

    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # --- Add tasks (intentionally out of order) ------------------------------
    mochi.add_task(Task("Evening walk", "17:00", 30, "medium", frequency="daily"))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", frequency="daily"))
    mochi.add_task(Task("Feeding", "08:15", 15, "high", frequency="daily"))
    mochi.add_task(Task("Grooming", "10:00", 45, "low"))
    mochi.add_task(Task("Vet appointment", "10:30", 60, "high"))

    whiskers.add_task(Task("Play session", "09:00", 20, "high", frequency="daily"))
    whiskers.add_task(Task("Feeding", "08:00", 10, "high", frequency="daily"))
    whiskers.add_task(Task("Litter box cleaning", "12:00", 10, "medium"))

    # --- Build scheduler -----------------------------------------------------
    scheduler = Scheduler(owner)

    # --- Display today's schedule --------------------------------------------
    print("=" * 60)
    print(f"  Today's Schedule for {owner.name}")
    print(f"  Pets: {', '.join(p.name for p in owner.pets)}")
    print("=" * 60)

    summary = scheduler.get_schedule_summary()

    for entry in summary["explanations"]:
        print(f"\n  {entry['task']}")
        print(f"    -> {entry['reason']}")

    print(f"\n" + "-" * 60)
    print(f"  Total tasks : {summary['total_tasks']}")
    print(f"  Total time  : {summary['total_minutes']} minutes")

    # --- Conflict detection --------------------------------------------------
    if summary["conflicts"]:
        print(f"\n  *** WARNINGS ***")
        for warning in summary["conflicts"]:
            print(f"  {warning}")
    else:
        print("\n  No scheduling conflicts detected.")

    # --- Demonstrate sorting by priority -------------------------------------
    print(f"\n{'=' * 60}")
    print("  Tasks sorted by priority:")
    print("=" * 60)
    for task in scheduler.sort_by_priority():
        print(f"  {task}")

    # --- Demonstrate filtering -----------------------------------------------
    print(f"\n{'=' * 60}")
    print("  Tasks for Mochi only:")
    print("=" * 60)
    for task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task}")

    # --- Demonstrate recurring task ------------------------------------------
    print(f"\n{'=' * 60}")
    print("  Marking 'Morning walk' complete...")
    print("=" * 60)
    morning_walk = mochi.tasks[1]  # "Morning walk"
    new_task = scheduler.mark_task_complete(morning_walk)
    print(f"  Completed: {morning_walk}")
    if new_task:
        print(f"  Next occurrence created: {new_task} (due {new_task.due_date})")

    print()


if __name__ == "__main__":
    main()
