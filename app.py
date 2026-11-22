"""Streamlit front end for PawPal+. Launch with: python -m streamlit run app.py"""
from datetime import date, datetime, time
import streamlit as st
from pawpal_system import FREQUENCIES, PRIORITIES, Owner, Pet, Scheduler, Task

st.set_page_config(page_title='PawPal+ | Daily care', page_icon='🐾', layout='centered')
st.title('🐾 PawPal+')
st.caption('A daily care planner for your household. Data lasts for this browser session only.')
if 'owner' not in st.session_state:
    st.session_state.owner = Owner('Jordan')
owner = st.session_state.owner
scheduler = Scheduler(owner)
with st.form('pet'):
    name = st.text_input('Pet name')
    species = st.selectbox('Species', ['dog', 'cat', 'other'])
    if st.form_submit_button('Add pet'):
        try:
            owner.add_pet(Pet(name, species))
            st.success('Pet added.')
        except ValueError as exc:
            st.error(str(exc))
if owner.pets:
    with st.form('task'):
        pet = st.selectbox('Pet', owner.pets, format_func=lambda p: p.name)
        description = st.text_input('Task description')
        day = st.date_input('Due date', date.today())
        start = st.time_input('Start time', time(8), step=60)
        duration = st.number_input('Duration (minutes)', 1, 240, 10)
        priority = st.selectbox('Priority', PRIORITIES, index=1)
        frequency = st.selectbox('Frequency', FREQUENCIES)
        if st.form_submit_button('Add task'):
            try:
                pet.add_task(Task(description, datetime.combine(day, start), duration, priority, frequency))
                st.success('Task added.')
            except ValueError as exc:
                st.error(str(exc))
for pet, task in scheduler.tasks_for_day(date.today()):
    st.text(f'{task.due:%H:%M} | {pet.name}: {task.description}')
