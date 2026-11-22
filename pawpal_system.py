"""Initial design: the UI will call these classes, not store its own task list."""
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(eq=False)
class Task:
    description: str
    due: datetime
    duration_minutes: int
    priority: str = 'medium'
    frequency: str = 'once'
    completed: bool = field(default=False, init=False)

    def mark_complete(self):
        raise NotImplementedError


@dataclass(eq=False)
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list, init=False)

    def add_task(self, task: Task):
        raise NotImplementedError


@dataclass(eq=False)
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list, init=False)

    def add_pet(self, pet: Pet):
        raise NotImplementedError

    def all_tasks(self):
        raise NotImplementedError


@dataclass
class Scheduler:
    owner: Owner

    def tasks_for_day(self, day: date):
        raise NotImplementedError
