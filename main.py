"""CLI-first demonstration of the same backend used by the web interface."""
from datetime import date, datetime, time
from pawpal_system import Owner, Pet, Task, Scheduler


def demo(day: date) -> None:
    """Exercise sorting, filters, warnings, budget, and recurrence for one sample day."""
    owner = Owner('Jordan', daily_minutes=25)
    dog, cat = Pet('Mochi', 'dog'), Pet('Pip', 'cat')
    owner.add_pet(dog)
    owner.add_pet(cat)
    # Intentionally insert the evening task before breakfast.
    dog.add_task(Task('Evening walk', datetime.combine(day, time(18)), 25, 'low'))
    breakfast = Task('Breakfast', datetime.combine(day, time(8)), 10, 'high', 'daily')
    dog.add_task(breakfast)
    cat.add_task(Task('Brush coat', datetime.combine(day, time(12)), 10, 'medium', 'weekly'))
    cat.add_task(Task('Puzzle feeder', datetime.combine(day, time(8)), 10, 'low'))
    scheduler = Scheduler(owner)
    print(f"Today's Schedule | {day} | {owner.name}")
    for pet, task in scheduler.tasks_for_day(day):
        print(f'{task.due:%H:%M}  {pet.name:<5}  {task.description:<13}  {task.duration_minutes:>2} min  {task.priority}')
    print('\nWarnings')
    for warning in scheduler.detect_conflicts(day):
        print(warning)
    print(f'\nDaily plan | {owner.daily_minutes} minutes')
    for pet, task, chosen, reason in scheduler.build_plan(day):
        print(f'{"Plan " if chosen else "Defer"}  {task.due:%H:%M}  {pet.name}: {task.description} — {reason}')
    following = scheduler.mark_task_complete(dog, breakfast, day)
    print('\nCompleted for Mochi today:')
    for _, task in scheduler.filter_tasks(day=day, pet_name='Mochi', completed=True):
        print(f'{task.due:%H:%M}  {task.description}')
    if following:
        print(f'Next: {dog.name} — {following.description} on {following.due:%Y-%m-%d at %H:%M} (pending)')


if __name__ == '__main__':
    demo(date.today())
