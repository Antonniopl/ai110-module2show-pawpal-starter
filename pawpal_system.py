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

    def mark_complete(self) -> None:
        """Record that this occurrence is finished."""
        self.completed = True


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


@dataclass(eq=False)
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Require a household owner name."""
        self.name = nonblank(self.name, 'Owner name')

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

    def tasks_for_day(self, day: date) -> list[tuple[Pet, Task]]:
        """Find the household's tasks due on the given day."""
        return [(p, t) for p, t in self.owner.all_tasks() if t.due.date() == day]
