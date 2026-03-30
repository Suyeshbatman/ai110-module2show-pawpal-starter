"""Tests for PawPal+ scheduling system."""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Task basics
# ---------------------------------------------------------------------------

class TestTask:
    def test_mark_complete(self):
        """Calling mark_complete() changes the task's status to True."""
        task = Task("Walk", "08:00", 30, "high")
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_priority_value(self):
        assert Task("A", "08:00", 10, "high").priority_value() == 3
        assert Task("B", "08:00", 10, "medium").priority_value() == 2
        assert Task("C", "08:00", 10, "low").priority_value() == 1

    def test_end_time_str(self):
        task = Task("Walk", "08:00", 45, "high")
        assert task.end_time_str() == "08:45"

    def test_create_next_occurrence_daily(self):
        task = Task("Feed", "09:00", 10, "high", frequency="daily", due_date=date(2026, 3, 29))
        next_task = task.create_next_occurrence()
        assert next_task is not None
        assert next_task.due_date == date(2026, 3, 30)
        assert next_task.completed is False
        assert next_task.frequency == "daily"

    def test_create_next_occurrence_weekly(self):
        task = Task("Grooming", "10:00", 60, "low", frequency="weekly", due_date=date(2026, 3, 29))
        next_task = task.create_next_occurrence()
        assert next_task is not None
        assert next_task.due_date == date(2026, 4, 5)

    def test_create_next_occurrence_once_returns_none(self):
        task = Task("Vet visit", "14:00", 60, "high", frequency="once")
        assert task.create_next_occurrence() is None


# ---------------------------------------------------------------------------
# Pet basics
# ---------------------------------------------------------------------------

class TestPet:
    def test_add_task_increases_count(self):
        """Adding a task to a Pet increases that pet's task count."""
        pet = Pet("Mochi", "dog")
        assert len(pet.tasks) == 0
        pet.add_task(Task("Walk", "08:00", 30, "high"))
        assert len(pet.tasks) == 1
        pet.add_task(Task("Feed", "09:00", 10, "high"))
        assert len(pet.tasks) == 2

    def test_remove_task(self):
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Walk", "08:00", 30, "high"))
        assert pet.remove_task("Walk") is True
        assert len(pet.tasks) == 0

    def test_get_pending_tasks(self):
        pet = Pet("Mochi", "dog")
        t1 = Task("Walk", "08:00", 30, "high")
        t2 = Task("Feed", "09:00", 10, "high")
        pet.add_task(t1)
        pet.add_task(t2)
        t1.mark_complete()
        pending = pet.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].description == "Feed"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class TestOwner:
    def test_get_all_tasks_across_pets(self):
        owner = Owner("Jordan")
        p1 = Pet("Mochi", "dog")
        p2 = Pet("Whiskers", "cat")
        p1.add_task(Task("Walk", "08:00", 30, "high"))
        p2.add_task(Task("Play", "09:00", 20, "medium"))
        owner.add_pet(p1)
        owner.add_pet(p2)
        assert len(owner.get_all_tasks()) == 2

    def test_get_pet_by_name(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog"))
        assert owner.get_pet_by_name("mochi") is not None
        assert owner.get_pet_by_name("unknown") is None


# ---------------------------------------------------------------------------
# Scheduler — sorting
# ---------------------------------------------------------------------------

class TestSchedulerSorting:
    def _make_scheduler(self) -> Scheduler:
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Evening walk", "17:00", 30, "medium"))
        pet.add_task(Task("Morning walk", "07:30", 30, "high"))
        pet.add_task(Task("Afternoon nap", "13:00", 60, "low"))
        owner.add_pet(pet)
        return Scheduler(owner)

    def test_sort_by_time(self):
        """Tasks are returned in chronological order."""
        s = self._make_scheduler()
        sorted_tasks = s.sort_by_time()
        times = [t.time for t in sorted_tasks]
        assert times == ["07:30", "13:00", "17:00"]

    def test_sort_by_priority(self):
        s = self._make_scheduler()
        sorted_tasks = s.sort_by_priority()
        priorities = [t.priority for t in sorted_tasks]
        assert priorities == ["high", "medium", "low"]


# ---------------------------------------------------------------------------
# Scheduler — filtering
# ---------------------------------------------------------------------------

class TestSchedulerFiltering:
    def test_filter_by_status(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        t1 = Task("Walk", "08:00", 30, "high")
        t2 = Task("Feed", "09:00", 10, "high")
        t1.mark_complete()
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        s = Scheduler(owner)
        assert len(s.filter_by_status(completed=True)) == 1
        assert len(s.filter_by_status(completed=False)) == 1

    def test_filter_by_pet(self):
        owner = Owner("Jordan")
        p1 = Pet("Mochi", "dog")
        p2 = Pet("Whiskers", "cat")
        p1.add_task(Task("Walk", "08:00", 30, "high"))
        p2.add_task(Task("Play", "09:00", 20, "medium"))
        owner.add_pet(p1)
        owner.add_pet(p2)
        s = Scheduler(owner)
        assert len(s.filter_by_pet("Mochi")) == 1
        assert len(s.filter_by_pet("Whiskers")) == 1
        assert len(s.filter_by_pet("Unknown")) == 0


# ---------------------------------------------------------------------------
# Scheduler — recurring tasks
# ---------------------------------------------------------------------------

class TestSchedulerRecurrence:
    def test_mark_complete_creates_next_daily(self):
        """Marking a daily task complete creates a new task for the following day."""
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        task = Task("Walk", "08:00", 30, "high", frequency="daily", due_date=date(2026, 3, 29))
        pet.add_task(task)
        owner.add_pet(pet)
        s = Scheduler(owner)

        new_task = s.mark_task_complete(task)

        assert task.completed is True
        assert new_task is not None
        assert new_task.due_date == date(2026, 3, 30)
        assert new_task.completed is False
        assert len(pet.tasks) == 2  # original + new occurrence

    def test_mark_complete_once_no_recurrence(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        task = Task("Vet", "14:00", 60, "high", frequency="once")
        pet.add_task(task)
        owner.add_pet(pet)
        s = Scheduler(owner)

        new_task = s.mark_task_complete(task)
        assert new_task is None
        assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Scheduler — conflict detection
# ---------------------------------------------------------------------------

class TestSchedulerConflicts:
    def test_detect_overlapping_tasks(self):
        """Scheduler flags tasks that overlap in time."""
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Grooming", "10:00", 45, "low"))
        pet.add_task(Task("Vet appointment", "10:30", 60, "high"))
        owner.add_pet(pet)
        s = Scheduler(owner)

        conflicts = s.detect_conflicts()
        assert len(conflicts) == 1
        assert "Grooming" in conflicts[0]
        assert "Vet appointment" in conflicts[0]

    def test_no_conflicts_when_tasks_dont_overlap(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Walk", "07:00", 30, "high"))
        pet.add_task(Task("Feed", "08:00", 15, "high"))
        owner.add_pet(pet)
        s = Scheduler(owner)

        assert len(s.detect_conflicts()) == 0

    def test_no_conflicts_with_empty_tasks(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog"))
        s = Scheduler(owner)
        assert len(s.detect_conflicts()) == 0


# ---------------------------------------------------------------------------
# Scheduler — schedule generation
# ---------------------------------------------------------------------------

class TestScheduleGeneration:
    def test_daily_schedule_excludes_completed(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        t1 = Task("Walk", "08:00", 30, "high")
        t2 = Task("Feed", "09:00", 10, "high")
        t1.mark_complete()
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        s = Scheduler(owner)

        schedule = s.get_daily_schedule()
        assert len(schedule) == 1
        assert schedule[0].description == "Feed"

    def test_explanation_has_reason_for_each_task(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Walk", "08:00", 30, "high"))
        pet.add_task(Task("Play", "09:00", 20, "medium"))
        owner.add_pet(pet)
        s = Scheduler(owner)

        explanations = s.generate_schedule_explanation()
        assert len(explanations) == 2
        for entry in explanations:
            assert len(entry["reason"]) > 0

    def test_summary_contains_all_fields(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Walk", "08:00", 30, "high"))
        owner.add_pet(pet)
        s = Scheduler(owner)

        summary = s.get_schedule_summary()
        assert "tasks" in summary
        assert "explanations" in summary
        assert "conflicts" in summary
        assert summary["total_tasks"] == 1
        assert summary["total_minutes"] == 30
