from datetime import datetime
from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task('Breakfast', datetime(2026, 11, 22, 8), 10)
    assert not task.completed
    task.mark_complete()
    assert task.completed


def test_add_task_increases_only_its_pets_count():
    dog, cat = Pet('Mochi', 'dog'), Pet('Pip', 'cat')
    task = Task('Walk', datetime(2026, 11, 22, 18), 25)
    dog.add_task(task)
    assert dog.tasks == [task]
    assert cat.tasks == []
