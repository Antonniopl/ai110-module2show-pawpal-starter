"""Pet care domain model. All times are local wall-clock times, at minute precision."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from uuid import uuid4

PRIORITIES = ('high', 'medium', 'low')
FREQUENCIES = ('once', 'daily', 'weekly')
PREFERENCES = ('earlier first', 'shorter first')


def nonblank(value: str, label: str) -> str:
    """Strip a required text field or report a useful validation error."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} cannot be blank.')
    return value.strip()


@dataclass(eq=False)
class Task:
    description: str
    due: datetime
    duration_minutes: int
    priority: str = 'medium'
    frequency: str = 'once'
    completed: bool = field(default=False, init=False)
    id: str = field(default_factory=lambda: uuid4().hex, init=False)

    def __post_init__(self) -> None:
        """Validate an occurrence before it enters a pet's schedule."""
        self.description = nonblank(self.description, 'Task description')
        if not isinstance(self.due, datetime) or self.due.tzinfo is not None:
            raise ValueError('Choose a local date and time without a time zone.')
        if self.due.second or self.due.microsecond:
            raise ValueError('Use whole minutes for the start time.')
        if type(self.duration_minutes) is not int or not 1 <= self.duration_minutes <= 240:
            raise ValueError('Duration must be 1–240 whole minutes.')
        if self.due.hour * 60 + self.due.minute + self.duration_minutes > 1440:
            raise ValueError('Tasks must finish by midnight on their scheduled day.')
        if self.priority not in PRIORITIES or self.frequency not in FREQUENCIES:
            raise ValueError('Choose a listed priority and frequency.')

    def mark_complete(self, today: date | None = None) -> Task | None:
        """Close once and return the next occurrence for the pet, if this repeats."""
        if self.completed:
            return None
        following = None
        if self.frequency != 'once':
            base = max(self.due.date(), today or date.today())
            try:
                following_day = base + timedelta(days=1 if self.frequency == 'daily' else 7)
            except OverflowError as exc:
                raise ValueError('The next occurrence falls outside the calendar.') from exc
            following = replace(self, due=datetime.combine(following_day, self.due.time()))
        self.completed = True
        return following

    def slot(self) -> tuple[int, int]:
        """Return start and exclusive end as minutes after midnight."""
        start = self.due.hour * 60 + self.due.minute
        return start, start + self.duration_minutes


@dataclass(eq=False)
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Require a pet name and species."""
        self.name = nonblank(self.name, 'Pet name')
        self.species = nonblank(self.species, 'Species')

    def add_task(self, task: Task) -> None:
        """Attach an occurrence once to this pet."""
        if task in self.tasks:
            raise ValueError('This occurrence is already on the list.')
        self.tasks.append(task)

    def edit_task(self, task: Task, replacement: Task) -> None:
        """Replace a pending task's details while preserving its occurrence ID."""
        if task not in self.tasks or task.completed or replacement.completed:
            raise ValueError('Only a pending task on this pet can be edited.')
        if replacement in self.tasks and replacement is not task:
            raise ValueError('Cannot replace a task with another stored occurrence.')
        replacement.id = task.id
        self.tasks[self.tasks.index(task)] = replacement


@dataclass(eq=False)
class Owner:
    name: str
    daily_minutes: int = 60
    preference: str = "earlier first"
    pets: list[Pet] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Require a household owner name."""
        self.configure(self.name, self.daily_minutes, self.preference)

    def configure(self, name: str, daily_minutes: int, preference: str) -> None:
        """Validate the whole profile before changing any saved setting."""
        name = nonblank(name, 'Owner name')
        if type(daily_minutes) is not int or not 0 <= daily_minutes <= 1440:
            raise ValueError('Daily time budget must be between 0 and 1440 whole minutes.')
        if preference not in PREFERENCES:
            raise ValueError('Choose a listed planning preference.')
        self.name, self.daily_minutes, self.preference = name, daily_minutes, preference

    def add_pet(self, pet: Pet) -> None:
        """Add a uniquely named pet to this household."""
        if any(p.name.casefold() == pet.name.casefold() for p in self.pets):
            raise ValueError('That pet name is already in use. Add a distinguishing nickname.')
        self.pets.append(pet)

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return pet–task pairs without duplicating the stored task records."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    owner: Owner

    def filter_tasks(self, *, day: date | None = None, pet_name: str | None = None,
                     completed: bool | None = None) -> list[tuple[Pet, Task]]:
        """Return records matching every supplied filter; None means all."""
        return [(p, t) for p, t in self.owner.all_tasks()
                if (day is None or t.due.date() == day)
                and (pet_name is None or p.name.casefold() == pet_name.strip().casefold())
                and (completed is None or t.completed == completed)]

    def sort_by_time(self, rows: list[tuple[Pet, Task]] | None = None) -> list[tuple[Pet, Task]]:
        """Sort a copy by full due date/time; keep insertion order for exact ties."""
        return sorted(self.owner.all_tasks() if rows is None else rows, key=lambda row: row[1].due)

    def tasks_for_day(self, day: date) -> list[tuple[Pet, Task]]:
        """Return the household's chronological agenda, including completed care."""
        return self.sort_by_time(self.filter_tasks(day=day))

    def mark_task_complete(self, pet: Pet, task: Task, today: date | None = None) -> Task | None:
        """Complete a known occurrence and attach its successor to the same pet once."""
        if pet not in self.owner.pets or task not in pet.tasks:
            raise ValueError('That task does not belong to this pet and household.')
        following = task.mark_complete(today)
        if following is not None:
            pet.add_task(following)
        return following

    def detect_conflicts(self, day: date) -> list[str]:
        """Warn once per start minute shared by two or more pending household tasks."""
        groups: dict[datetime, list[str]] = {}
        for pet, task in self.filter_tasks(day=day, completed=False):
            groups.setdefault(task.due, []).append(f'{pet.name}: {task.description}')
        return [f'{start:%H:%M} conflict — ' + '; '.join(groups[start])
                for start in sorted(groups) if len(groups[start]) > 1]

    def build_plan(self, day: date) -> list[tuple[Pet, Task, bool, str]]:
        """Select feasible pending tasks by priority, then explain every decision in time order."""
        pending = self.filter_tasks(day=day, completed=False)
        done = self.filter_tasks(day=day, completed=True)
        remaining = max(0, self.owner.daily_minutes - sum(t.duration_minutes for _, t in done))
        reserved = [t.slot() for _, t in done]

        def rank(row: tuple[Pet, Task]) -> tuple:
            task = row[1]
            tie = task.duration_minutes if self.owner.preference == 'shorter first' else 0
            return PRIORITIES.index(task.priority), tie, task.due

        decisions = []
        for pet, task in sorted(pending, key=rank):
            start, end = task.slot()
            if any(start < stop and begin < end for begin, stop in reserved):
                chosen, reason = False, 'Overlaps a reserved time slot.'
            elif task.duration_minutes > remaining:
                chosen, reason = False, f'Needs {task.duration_minutes} min; only {remaining} min left.'
            else:
                remaining -= task.duration_minutes
                reserved.append((start, end))
                chosen, reason = True, f'{task.priority.capitalize()} priority; fits time and budget.'
            decisions.append((pet, task, chosen, reason))
        return sorted(decisions, key=lambda row: row[1].due)
