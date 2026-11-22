"""Run a small household through the same model used by the interface."""
from datetime import date, datetime, time
from pawpal_system import Owner, Pet, Task, Scheduler


def demo(day: date) -> None:
    """Display a sample day in the terminal."""
    owner = Owner('Jordan')
    dog, cat = Pet('Mochi', 'dog'), Pet('Pip', 'cat')
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task('Evening walk', datetime.combine(day, time(18)), 25, 'low'))
    dog.add_task(Task('Breakfast', datetime.combine(day, time(8)), 10, 'high', 'daily'))
    cat.add_task(Task('Brush coat', datetime.combine(day, time(12)), 10, 'medium', 'weekly'))
    print(f"Today's Schedule | {day}")
    for pet, task in Scheduler(owner).tasks_for_day(day):
        print(f'{task.due:%H:%M} | {pet.name}: {task.description}')


if __name__ == '__main__':
    demo(date.today())
