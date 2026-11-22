"""Native Streamlit smoke test; installing requirements enables this test."""
from datetime import date, timedelta
from pathlib import Path
import pytest


def test_native_streamlit_add_schedule_complete_and_view_next_day():
    pytest.importorskip('streamlit', reason='Install requirements.txt for the native Streamlit integration test.')
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).parents[1] / 'app.py')).run()
    assert not app.exception
    app.radio(key='page').set_value('Household').run()
    app.text_input(key='pet_name').set_value('Mochi')
    next(b for b in app.button if b.label == 'Add pet').click().run()
    assert [p.name for p in app.session_state['owner'].pets] == ['Mochi']
    app.radio(key='page').set_value('Care tasks').run()
    app.text_input(key='new_desc').set_value('Breakfast')
    app.selectbox(key='new_frequency').select('daily')
    next(b for b in app.button if b.label == 'Add task').click().run()
    app.radio(key='page').set_value('Daily schedule').run()
    next(b for b in app.button if b.label == 'Mark complete').click().run()
    app.date_input(key='view_day').set_value(date.today() + timedelta(days=1)).run()
    assert not app.exception
    assert app.table[0].value.iloc[0]['Task'] == 'Breakfast'
    assert app.table[0].value.iloc[0]['Status'] == 'Pending'
