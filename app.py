"""Run with python -m streamlit run app.py. The model owns the data and the rules."""
from datetime import date, datetime, time

import streamlit as st

from pawpal_system import (
    FREQUENCIES, PREFERENCES, PRIORITIES, Owner, Pet, Scheduler, Task,
)


def household(owner: Owner) -> None:
    """Edit household settings and register pets without replacing the owner."""
    st.header('Household')
    with st.form('profile'):
        name = st.text_input('Owner name', value=owner.name, key='owner_name')
        minutes = st.number_input('Daily care budget (minutes)', 0, 1440, owner.daily_minutes)
        preference = st.selectbox('For tasks with equal priority', PREFERENCES,
                                  index=PREFERENCES.index(owner.preference))
        if st.form_submit_button('Save settings'):
            try:
                owner.configure(name, minutes, preference)
                st.success('Household settings saved.')
            except ValueError as exc:
                st.error(str(exc))
    st.subheader('Add a pet')
    with st.form('pet'):
        name = st.text_input('Pet name', key='pet_name')
        species = st.selectbox('Species', ['dog', 'cat', 'other'])
        if st.form_submit_button('Add pet'):
            try:
                owner.add_pet(Pet(name, species))
                st.success('Pet added. Open Care tasks to schedule its first activity.')
            except ValueError as exc:
                st.error(str(exc))
    if owner.pets:
        st.table([{'Pet': p.name, 'Species': p.species, 'Tasks': len(p.tasks)} for p in owner.pets])


def task_form(pet: Pet, original: Task | None) -> None:
    """Create or edit an occurrence using one set of validated inputs."""
    prefix = 'edit_' + original.id if original else 'new'
    with st.form(prefix):
        desc = st.text_input('Task description', value=original.description if original else '',
                             key=prefix + '_desc')
        a, b = st.columns(2)
        day = a.date_input('Due date', value=original.due.date() if original else date.today(), key=prefix + '_date')
        start = b.time_input('Start time', value=original.due.time() if original else time(8),
                             step=60, key=prefix + '_time')
        duration = st.number_input('Duration (minutes)', 1, 240, original.duration_minutes if original else 10,
                                   key=prefix + '_duration')
        priority = st.selectbox('Priority', PRIORITIES, index=PRIORITIES.index(original.priority) if original else 1,
                                key=prefix + '_priority')
        frequency = st.selectbox('Frequency', FREQUENCIES, index=FREQUENCIES.index(original.frequency) if original else 0,
                                 key=prefix + '_frequency')
        if st.form_submit_button('Save changes' if original else 'Add task'):
            try:
                updated = Task(desc, datetime.combine(day, start), duration, priority, frequency)
                if original:
                    pet.edit_task(original, updated)
                else:
                    pet.add_task(updated)
                st.success(f'Saved for {pet.name} on {day} at {start:%H:%M}.')
            except ValueError as exc:
                st.error(str(exc))


def care_tasks(owner: Owner) -> None:
    """Choose a pet and either create a task or update a pending one."""
    st.header('Care tasks')
    if not owner.pets:
        st.info('Start in Household and add a pet first.')
        return
    pets = {p.name: p for p in owner.pets}
    pet = pets[st.selectbox('Pet', list(pets), key='care_pet')]
    mode = st.radio('Action', ['Add', 'Edit'], horizontal=True)
    original = None
    if mode == 'Edit':
        pending = {t.id: t for t in pet.tasks if not t.completed}
        if not pending:
            st.info('This pet has no pending tasks to edit.')
            return
        key = st.selectbox('Pending task', list(pending), key='edit_choice', format_func=lambda k:
                           f'{pending[k].due:%b %d, %H:%M} · {pending[k].description} · {k[:5]}')
        original = pending[key]
    task_form(pet, original)


def agenda(owner: Owner, scheduler: Scheduler) -> None:
    """Show the real agenda, resolved and unresolved conflicts, and budget decisions."""
    st.header('Daily schedule')
    if 'notice' in st.session_state:
        st.success(st.session_state.pop('notice'))
    if not owner.pets:
        st.info('Your schedule is empty. Go to Household to add your first pet.')
        return
    day = st.date_input('View date', value=date.today(), key='view_day')
    st.caption(f'{owner.name} · {owner.daily_minutes} minutes per day · equal priority: {owner.preference}')
    for warning in scheduler.detect_conflicts(day):
        st.warning(warning + '. Edit a pending task in Care tasks to change its start.')
    a, b = st.columns(2)
    pet_name = a.selectbox('Filter by pet', [None, *[p.name for p in owner.pets]],
                           format_func=lambda p: 'All pets' if p is None else p, key='view_pet')
    statuses = {'All': None, 'Pending': False, 'Completed': True}
    status = b.selectbox('Filter by status', list(statuses), key='view_status')
    rows = scheduler.sort_by_time(scheduler.filter_tasks(day=day, pet_name=pet_name, completed=statuses[status]))
    if rows:
        st.table([{'Time': t.due.strftime('%H:%M'), 'Pet': p.name, 'Task': t.description,
                   'Min': t.duration_minutes, 'Priority': t.priority, 'Repeats': t.frequency,
                   'Status': 'Done' if t.completed else 'Pending'} for p, t in rows])
    else:
        st.info('No tasks match this date and these filters.')
    pending = {t.id: (p, t) for p, t in rows if not t.completed}
    if pending:
        def label(key: str) -> str:
            p, t = pending[key]
            return f'{t.due:%H:%M} · {p.name} · {t.description} · {key[:5]}'
        key = st.selectbox('Occurrence to complete', list(pending), format_func=label, key='complete_choice')
        if st.button('Mark complete'):
            p, t = pending[key]
            try:
                following = scheduler.mark_task_complete(p, t)
                message = f'Completed {t.description} for {p.name}.'
                if following:
                    message += f' Next occurrence: {following.due:%Y-%m-%d at %H:%M}.'
                st.session_state.notice = message
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    st.subheader('Household plan')
    st.caption('For all pets on this date, regardless of filters. Deferred tasks stay on the agenda until you edit or finish them.')
    plan = scheduler.build_plan(day)
    if plan:
        st.table([{'Time': t.due.strftime('%H:%M'), 'Pet': p.name, 'Task': t.description,
                   'Decision': 'Plan' if chosen else 'Defer', 'Reason': why} for p, t, chosen, why in plan])
    else:
        st.info('No pending care to plan for this day.')


def main() -> None:
    """Keep one owner per session and route the selected view."""
    st.set_page_config(page_title='PawPal+ | Daily care', page_icon='🐾', layout='centered')
    st.title('🐾 PawPal+')
    st.caption('PET CARE PLANNER  ·  Changes last for this browser session only.')
    if 'owner' not in st.session_state:
        st.session_state.owner = Owner('Jordan')
    owner = st.session_state.owner
    page = st.radio('Navigate', ['Daily schedule', 'Household', 'Care tasks'], horizontal=True, key='page')
    if page == 'Household':
        household(owner)
    elif page == 'Care tasks':
        care_tasks(owner)
    else:
        agenda(owner, Scheduler(owner))


if __name__ == '__main__':
    main()
