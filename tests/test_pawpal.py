from datetime import date, datetime, timedelta

import pytest
from pawpal_system import Owner, Pet, Scheduler, Task


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


DAY = date(2026, 12, 31)


def care(name='Meal', clock='08:00', minutes=10, priority='medium', frequency='once', day=DAY):
    return Task(name, datetime.fromisoformat(f'{day}T{clock}'), minutes, priority, frequency)


@pytest.fixture
def home():
    owner = Owner('Jordan', 30)
    dog, cat = Pet('Mochi', 'dog'), Pet('Pip', 'cat')
    owner.add_pet(dog)
    owner.add_pet(cat)
    return Scheduler(owner), dog, cat


def test_sort_handles_dates_and_stable_ties_without_mutating_source(home):
    s, dog, cat = home
    late, early, tie, tomorrow = care(clock='18:00'), care(), care('Brush'), care(day=DAY + timedelta(days=1))
    for task in [late, early, tomorrow]:
        dog.add_task(task)
    cat.add_task(tie)
    assert [t for _, t in s.sort_by_time()] == [early, tie, late, tomorrow]
    assert dog.tasks == [late, early, tomorrow]
    assert [t for _, t in s.tasks_for_day(DAY)] == [early, tie, late]
    assert s.sort_by_time([]) == []


def test_filters_combine_pet_date_and_status(home):
    s, dog, cat = home
    for pet in (dog, cat):
        pet.add_task(care())
    dog.add_task(care(day=DAY + timedelta(days=1)))
    s.mark_task_complete(dog, dog.tasks[0], DAY)
    assert s.filter_tasks(day=DAY, pet_name=' moCHI ', completed=True) == [(dog, dog.tasks[0])]
    assert s.filter_tasks(day=DAY, completed=False) == [(cat, cat.tasks[0])]
    assert s.filter_tasks(pet_name='absent') == []


@pytest.mark.parametrize('freq,days', [('daily', 1), ('weekly', 7)])
def test_recurrence_advances_date_retains_fields_and_is_idempotent(home, freq, days):
    s, dog, cat = home
    original = care(frequency=freq)
    dog.add_task(original)
    nxt = s.mark_task_complete(dog, original, DAY)
    assert original.completed and not nxt.completed and nxt.id != original.id
    assert nxt.due == original.due + timedelta(days=days)
    assert (nxt.description, nxt.duration_minutes, nxt.priority, nxt.frequency) == ('Meal', 10, 'medium', freq)
    assert s.mark_task_complete(dog, original, DAY) is None
    assert dog.tasks == [original, nxt] and not cat.tasks


@pytest.mark.parametrize('offset,expected', [(3, 4), (-3, 1)])
def test_late_and_early_completion_never_generate_a_stale_successor(home, offset, expected):
    s, dog, _ = home
    task = care(frequency='daily')
    dog.add_task(task)
    assert s.mark_task_complete(dog, task, DAY + timedelta(days=offset)).due.date() == DAY + timedelta(days=expected)


def test_once_and_wrong_pet(home):
    s, dog, cat = home
    task = care()
    dog.add_task(task)
    with pytest.raises(ValueError):
        s.mark_task_complete(cat, task, DAY)
    assert not task.completed
    assert s.mark_task_complete(dog, task, DAY) is None
    assert dog.tasks == [task]


def test_conflict_group_includes_same_and_different_pets_but_not_other_dates_or_done(home):
    s, dog, cat = home
    for pet, task in [(dog, care('Walk')), (dog, care('Water')), (cat, care('Brush')),
                      (cat, care('Tomorrow', day=DAY + timedelta(days=1)))]:
        pet.add_task(task)
    assert s.detect_conflicts(DAY) == ['08:00 conflict — Mochi: Walk; Mochi: Water; Pip: Brush']
    s.mark_task_complete(cat, cat.tasks[0], DAY)
    assert s.detect_conflicts(DAY) == ['08:00 conflict — Mochi: Walk; Mochi: Water']
    s.mark_task_complete(dog, dog.tasks[0], DAY)
    assert not s.detect_conflicts(DAY)


def test_plan_preserves_agenda_and_respects_priority_overlap_and_budget(home):
    s, dog, cat = home
    low, high, adjacent, too_long = (care('Puzzle', '08:00', 15, 'low'), care('Meal', '08:10', 10, 'high'),
                                     care('Play', '08:20', 20), care('Walk', '12:00', 15, 'low'))
    for p, t in [(dog, low), (cat, high), (dog, adjacent), (dog, too_long)]:
        p.add_task(t)
    plan = s.build_plan(DAY)
    assert [t for _, t, chosen, _ in plan if chosen] == [high, adjacent]
    assert plan[0][3].startswith('Overlaps') and '0 min left' in plan[-1][3]
    assert len(s.filter_tasks(completed=False)) == 4 and plan == s.build_plan(DAY)


def test_preference_breaks_priority_tie_and_skips_unaffordable_item(home):
    s, dog, _ = home
    early, small = care(minutes=15), care(clock='10:00', minutes=10)
    dog.add_task(early); dog.add_task(small)
    for preference, budget, expected in [('earlier first', 15, early), ('shorter first', 15, small), ('earlier first', 10, small)]:
        s.owner.configure('Jordan', budget, preference)
        assert [t for _, t, ok, _ in s.build_plan(DAY) if ok] == [expected]


def test_completed_care_consumes_budget_and_time_slot(home):
    s, dog, _ = home
    done = care(minutes=25)
    dog.add_task(done); dog.add_task(care('Overlap')); dog.add_task(care(clock='14:00'))
    s.mark_task_complete(dog, done, DAY)
    plan = s.build_plan(DAY)
    assert not any(ok for _, _, ok, _ in plan)
    assert 'Overlaps' in plan[0][3] and '5 min left' in plan[1][3]


def test_zero_budget_is_not_unlimited(home):
    s, dog, _ = home
    dog.add_task(care())
    s.owner.configure('Jordan', 0, 'earlier first')
    assert not s.build_plan(DAY)[0][2]


def test_empty_household_and_pet(home):
    for s in [Scheduler(Owner('Alex')), home[0]]:
        assert s.tasks_for_day(DAY) == s.build_plan(DAY) == s.detect_conflicts(DAY) == []


def test_edit_preserves_id_and_updates_original_pet(home):
    s, dog, _ = home
    original, updated = care(), care('New walk', clock='18:00', minutes=20, priority='high')
    dog.add_task(original); dog.edit_task(original, updated)
    assert dog.tasks == [updated] and original.id == updated.id
    s.mark_task_complete(dog, updated, DAY)
    with pytest.raises(ValueError):
        dog.edit_task(updated, care())


@pytest.mark.parametrize('kwargs', [dict(name=' '), dict(minutes=0), dict(minutes=241), dict(minutes=True),
                                   dict(priority='urgent'), dict(frequency='never'), dict(clock='23:58', minutes=3)])
def test_invalid_task_rejected(kwargs):
    with pytest.raises(ValueError):
        care(**kwargs)


def test_midnight_boundary_and_calendar_overflow(home):
    s, dog, _ = home
    assert care(clock='23:58', minutes=2).slot() == (1438, 1440)
    task = care(day=date.max, frequency='daily'); dog.add_task(task)
    with pytest.raises(ValueError):
        s.mark_task_complete(dog, task, date.max)
    assert not task.completed and dog.tasks == [task]


def test_profile_and_duplicate_name_validation_are_atomic(home):
    s, dog, _ = home
    with pytest.raises(ValueError):
        s.owner.add_pet(Pet(' MOCHI ', 'other'))
    with pytest.raises(ValueError):
        s.owner.configure('New', -1, 'earlier first')
    assert s.owner.name == 'Jordan' and len(s.owner.pets) == 2
    task = care(); dog.add_task(task)
    with pytest.raises(ValueError):
        dog.add_task(task)
