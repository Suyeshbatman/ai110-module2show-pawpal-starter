# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design centered around four core classes that model the real-world relationships in pet care:

- **Task** (dataclass): Represents a single care activity. Holds `description`, `time` (HH:MM), `duration_minutes`, `priority`, `frequency`, `completed`, and `due_date`. Responsible for marking itself complete, computing a numeric priority value, calculating its end time, and creating the next recurring occurrence.
- **Pet** (dataclass): Stores pet details (`name`, `species`, `age`) and owns a list of `Task` objects. Responsible for adding/removing tasks and returning pending (incomplete) tasks.
- **Owner** (dataclass): Represents the pet owner with a `name` and a list of `Pet` objects. Responsible for adding pets, looking up a pet by name, and aggregating all tasks across every pet.
- **Scheduler**: The "brain" of the system. Takes an `Owner` and provides sorting (by time or priority), filtering (by pet or completion status), conflict detection (overlapping time windows), recurring-task management, and daily schedule generation with human-readable explanations.

The key relationships are: an Owner *has many* Pets, a Pet *has many* Tasks, and the Scheduler *uses* an Owner to access all data.

**b. Design changes**

Yes. The original starter UI stored tasks as simple dictionaries with only `title`, `duration_minutes`, and `priority`. During implementation I expanded the Task model significantly to include `time` (HH:MM scheduling), `frequency` (once/daily/weekly), `completed` status, and `due_date`. This was necessary because the project requirements call for conflict detection (which needs actual times), recurring tasks (which need frequency and dates), and filtering by completion status. The UI in `app.py` was updated to collect these additional fields.

I also added a `ScheduledTask`-style explanation system directly into the Scheduler rather than creating a separate wrapper class. Keeping the explanations as dictionaries (`{"task": ..., "reason": ...}`) was simpler and avoided an extra class that would only hold two fields.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers the following constraints:

- **Time of day**: Tasks have explicit start times in HH:MM format. The scheduler sorts tasks chronologically to produce a readable daily timeline.
- **Priority level**: Tasks are ranked as high, medium, or low. Priority sorting lets the owner see what matters most, and the explanation text gives guidance on whether a task can be skipped or rescheduled.
- **Duration and overlap**: The scheduler calculates each task's time window (start to start + duration) and flags conflicts where two tasks overlap.
- **Completion status**: Only pending (incomplete) tasks appear in the generated schedule.
- **Recurrence**: Daily and weekly tasks automatically create their next occurrence when marked complete, so the owner doesn't have to re-enter them.

I prioritized time-based ordering as the primary sort for the daily schedule because a chronological view is most practical for a pet owner following a plan throughout the day. Priority sorting is available as a secondary view.

**b. Tradeoffs**

One key tradeoff is that the conflict detection checks for *overlapping time windows* but does not automatically resolve conflicts. It only issues warnings. This means if "Grooming" (10:00-10:45) overlaps with "Vet appointment" (10:30-11:30), the scheduler flags it but leaves both tasks in the schedule.

This is reasonable because automatic resolution (e.g., shifting one task) could produce unexpected results — the owner knows their real-world constraints better than the algorithm. A warning empowers the owner to decide whether to reschedule, rather than the system making assumptions. For a more advanced version, the scheduler could suggest alternative time slots.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI (Claude Code) throughout the project for:

- **Design brainstorming**: Exploring which classes were needed, what attributes they should hold, and how the Scheduler should retrieve tasks from the Owner's pets.
- **Code generation**: Generating the full implementation of `pawpal_system.py`, `main.py`, `app.py`, and the test suite based on the project requirements.
- **Debugging**: Fixing a Windows-specific Unicode encoding error (em-dash characters failing on cp1252 terminal encoding) that appeared when running `main.py`.
- **Test design**: Identifying key behaviors to test task completion, recurrence logic, conflict detection, sorting correctness, and schedule generation.

The most helpful prompts were specific and scoped: "implement these four classes with these responsibilities" and "write tests covering sorting, recurrence, and conflict detection." Broad prompts like "build the whole app" were less useful than targeted requests for individual pieces.

**b. Judgment and verification**

When generating the initial plan, the AI suggested a more complex approach with separate `models.py` and `scheduler.py` files, time-block-based scheduling (Morning/Afternoon/Evening blocks with minute budgets), and an `available_minutes` constraint. I chose to simplify this: the project spec calls for time-based scheduling with HH:MM task times, not abstract time blocks. A single `pawpal_system.py` file is cleaner for a course project and matches the phase instructions. I verified this decision by re-reading the project phases and confirming they reference `pawpal_system.py` as the logic layer.

---

## 4. Testing and Verification

**a. What you tested**

The test suite (23 tests in `tests/test_pawpal.py`) covers:

- **Task basics**: `mark_complete()` changes status, `priority_value()` returns correct numeric values, `end_time_str()` computes correctly, and `create_next_occurrence()` handles daily, weekly, and one-time tasks.
- **Pet operations**: Adding tasks increases count, removing tasks works, and `get_pending_tasks()` correctly filters by completion status.
- **Owner aggregation**: `get_all_tasks()` collects tasks across multiple pets, and `get_pet_by_name()` handles case-insensitive lookup and missing pets.
- **Scheduler sorting**: `sort_by_time()` returns chronological order, `sort_by_priority()` returns high-to-low order.
- **Scheduler filtering**: Filtering by completion status and by pet name.
- **Recurrence**: Marking a daily task complete creates a next-day occurrence; one-time tasks don't recur.
- **Conflict detection**: Overlapping tasks are flagged, non-overlapping tasks pass cleanly, and empty task lists produce no false positives.
- **Schedule generation**: Completed tasks are excluded, every scheduled task has a non-empty reason, and the summary contains all expected fields.

These tests are important because they verify the core contract of each class, if sorting, filtering, or conflict detection breaks, the entire app produces wrong output.

**b. Confidence**

I'm fairly confident (4/5) that the scheduler works correctly for its intended use cases. All 23 tests pass and cover the main happy paths and several edge cases.

Edge cases I would test next with more time:
- Tasks that span midnight (e.g., "23:30" with 60-minute duration)
- Tasks with identical times and descriptions (duplicate detection)
- Very large numbers of tasks (performance)
- Invalid time formats passed to the scheduler (robustness)
- Weekly recurrence across month/year boundaries

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the Scheduler class design. It cleanly separates concerns, sorting, filtering, conflict detection, and explanation generation are all independent methods that can be composed together. The `get_schedule_summary()` method ties everything into a single call that the UI consumes, which made the Streamlit integration straightforward.

**b. What you would improve**

If I had another iteration, I would:
- Add automatic conflict resolution suggestions (e.g., "Move Grooming to 11:30 to avoid overlap with Vet appointment")
- Store data persistently (database or file) so tasks survive between Streamlit sessions
- Add task editing in the UI (currently you can only add and complete tasks, not modify them)
- Support multiple owners or a login system
- Add calendar-view visualization of the daily schedule

**c. Key takeaway**

The most important lesson was the value of designing the data model first. Getting `Task`, `Pet`, `Owner`, and `Scheduler` right with clear responsibilities made every subsequent step implementation, testing, UI integration, dramatically easier. When the classes have clean interfaces, the UI becomes a thin layer that just calls methods and displays results, rather than containing business logic itself.
