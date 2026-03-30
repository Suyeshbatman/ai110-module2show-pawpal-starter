"""PawPal+ logic layer - all backend classes for the pet care scheduling system."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care activity."""
    description: str
    time: str  # "HH:MM" format
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    frequency: str = "once"  # "once", "daily", "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def priority_value(self) -> int:
        """Return numeric priority for sorting (high=3, medium=2, low=1)."""
        return {"high": 3, "medium": 2, "low": 1}.get(self.priority, 0)

    def create_next_occurrence(self) -> Optional["Task"]:
        """Create the next recurring instance of this task, or None if it's a one-time task."""
        if self.frequency == "daily":
            next_date = self.due_date + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = self.due_date + timedelta(weeks=1)
        else:
            return None
        return Task(
            description=self.description,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
            due_date=next_date,
        )

    def end_time_str(self) -> str:
        """Return the end time as 'HH:MM' based on start time + duration."""
        start = _parse_time(self.time)
        end = start + timedelta(minutes=self.duration_minutes)
        return end.strftime("%H:%M")

    def __str__(self) -> str:
        status = "Done" if self.completed else "Pending"
        return (
            f"{self.time} - {self.description} "
            f"({self.duration_minutes}min, {self.priority} priority, {status})"
        )


@dataclass
class Pet:
    """Stores pet details and its list of care tasks."""
    name: str
    species: str  # "dog", "cat", "other"
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a care task for this pet."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove a task by description. Returns True if found and removed."""
        for i, t in enumerate(self.tasks):
            if t.description == description:
                self.tasks.pop(i)
                return True
        return False

    def get_pending_tasks(self) -> list:
        """Return all incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def __str__(self) -> str:
        return f"{self.name} ({self.species}, age {self.age})"


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""
    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet_by_name(self, name: str) -> Optional[Pet]:
        """Find a pet by name (case-insensitive)."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Retrieve every task across all pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def __str__(self) -> str:
        pet_names = ", ".join(p.name for p in self.pets) or "no pets"
        return f"{self.name} (pets: {pet_names})"


class Scheduler:
    """The brain - retrieves, organizes, and manages tasks across all pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    # --- Retrieval -----------------------------------------------------------

    def get_all_tasks(self) -> list[Task]:
        """Get every task from every pet."""
        return self.owner.get_all_tasks()

    # --- Sorting -------------------------------------------------------------

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks chronologically by their 'HH:MM' time field."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks by priority, highest first."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return sorted(tasks, key=lambda t: t.priority_value(), reverse=True)

    # --- Filtering -----------------------------------------------------------

    def filter_by_status(self, completed: bool, tasks: list[Task] | None = None) -> list[Task]:
        """Filter tasks by completion status."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return [t for t in tasks if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return tasks belonging to a specific pet."""
        pet = self.owner.get_pet_by_name(pet_name)
        return list(pet.tasks) if pet else []

    # --- Recurring tasks -----------------------------------------------------

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete. If it recurs, create and return the next occurrence."""
        task.mark_complete()
        if task.frequency in ("daily", "weekly"):
            new_task = task.create_next_occurrence()
            if new_task:
                for pet in self.owner.pets:
                    if task in pet.tasks:
                        pet.add_task(new_task)
                        return new_task
        return None

    # --- Conflict detection --------------------------------------------------

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Detect overlapping tasks and return warning messages."""
        if tasks is None:
            tasks = self.get_all_tasks()
        pending = [t for t in tasks if not t.completed]
        sorted_tasks = self.sort_by_time(pending)
        warnings: list[str] = []

        for i in range(len(sorted_tasks)):
            for j in range(i + 1, len(sorted_tasks)):
                t1 = sorted_tasks[i]
                t2 = sorted_tasks[j]
                t1_start = _parse_time(t1.time)
                t1_end = t1_start + timedelta(minutes=t1.duration_minutes)
                t2_start = _parse_time(t2.time)
                if t2_start < t1_end:
                    warnings.append(
                        f"Conflict: '{t1.description}' ({t1.time}-{t1.end_time_str()}) "
                        f"overlaps with '{t2.description}' ({t2.time}-{t2.end_time_str()})"
                    )
        return warnings

    # --- Schedule generation -------------------------------------------------

    def get_daily_schedule(self) -> list[Task]:
        """Return today's pending tasks sorted by time."""
        pending = self.filter_by_status(completed=False)
        return self.sort_by_time(pending)

    def generate_schedule_explanation(self) -> list[dict]:
        """Generate the daily schedule with a reason for each task's placement."""
        schedule = self.get_daily_schedule()
        conflicts = self.detect_conflicts()
        explanations: list[dict] = []

        for i, task in enumerate(schedule):
            reason = (
                f"#{i + 1} - '{task.description}' at {task.time} "
                f"({task.duration_minutes}min, {task.priority} priority)"
            )
            if task.priority == "high":
                reason += " - High priority, should not be skipped."
            elif task.priority == "medium":
                reason += " - Medium priority, schedule if time permits."
            else:
                reason += " - Low priority, can be rescheduled if needed."

            if task.frequency != "once":
                reason += f" Recurs {task.frequency}."

            explanations.append({"task": task, "reason": reason})

        return explanations

    def get_schedule_summary(self) -> dict:
        """Return a summary dict with schedule stats, explanations, and conflicts."""
        explanations = self.generate_schedule_explanation()
        conflicts = self.detect_conflicts()
        schedule = self.get_daily_schedule()
        total_minutes = sum(t.duration_minutes for t in schedule)

        return {
            "tasks": schedule,
            "explanations": explanations,
            "conflicts": conflicts,
            "total_tasks": len(schedule),
            "total_minutes": total_minutes,
        }


# --- Module-level helper -----------------------------------------------------

def _parse_time(time_str: str) -> datetime:
    """Parse an 'HH:MM' string into a datetime for today."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    parts = time_str.split(":")
    return today.replace(hour=int(parts[0]), minute=int(parts[1]))
