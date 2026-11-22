"""Exercise our form handlers on reruns, without pretending to test Streamlit itself."""
from contextlib import nullcontext
from datetime import date, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


class State(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class Rerun(Exception):
    pass


class Controls:
    """Small script driver: feed widget answers and capture notices and displayed rows."""
    def __init__(self):
        self.session_state = State()
        self.messages = []
        self.tables = []

    def start(self, answers, clicked=''):
        self.answers, self.clicked = answers, clicked
        self.messages.clear()
        self.tables.clear()

    def selectbox(self, label, options, index=0, **kwargs):
        answer = self.answers.get(label, options[index])
        assert answer in options
        return answer

    radio = selectbox

    def text_input(self, label, value='', **kwargs):
        return self.answers.get(label, value)

    date_input = time_input = text_input

    def number_input(self, label, low, high, value, **kwargs):
        return self.answers.get(label, value)

    def button(self, label): return self.clicked == label
    form_submit_button = button
    def form(self, name): return nullcontext()
    def columns(self, number): return [self] * number
    def table(self, rows): self.tables.append(rows)
    def note(self, message): self.messages.append(message)
    warning = info = error = success = note
    def noop(self, *args, **kwargs): pass
    header = subheader = caption = title = set_page_config = noop
    def rerun(self): raise Rerun


def test_actual_form_handlers_keep_context_across_reruns(monkeypatch):
    ui = Controls()
    monkeypatch.setitem(sys.modules, 'streamlit', ui)
    spec = spec_from_file_location('pawpal_ui_wiring', Path(__file__).parents[1] / 'app.py')
    app = module_from_spec(spec); spec.loader.exec_module(app)

    def visit(page, clicked='', **answers):
        ui.start({'Navigate': page, **answers}, clicked)
        try:
            app.main()
        except Rerun:
            ui.start({'Navigate': page, **answers}, '')
            app.main()

    visit('Daily schedule')
    assert any('first pet' in m for m in ui.messages)
    visit('Household', 'Save settings', **{'Owner name': 'Alex', 'Daily care budget (minutes)': 12})
    for name in ('Mochi', 'Pip'):
        visit('Household', 'Add pet', **{'Pet name': name})
    visit('Care tasks', 'Add task', **{'Pet': 'Mochi', 'Task description': 'Breakfast', 'Frequency': 'daily'})
    visit('Care tasks', 'Add task', **{'Pet': 'Pip', 'Task description': 'Play'})
    visit('Care tasks', 'Save changes', **{'Pet': 'Pip', 'Action': 'Edit', 'Task description': 'Puzzle', 'Duration (minutes)': 5})
    visit('Daily schedule', **{'Filter by pet': 'Pip'})
    assert ui.tables[0][0]['Task'] == 'Puzzle' and len(ui.tables[0]) == 1
    assert any('08:00 conflict' in m for m in ui.messages)
    assert [row['Decision'] for row in ui.tables[1]] == ['Plan', 'Defer']
    visit('Daily schedule', 'Mark complete', **{'Filter by pet': 'Mochi'})
    assert any('Next occurrence:' in m for m in ui.messages)
    assert ui.tables[0][0]['Status'] == 'Done'
    assert not any('08:00 conflict' in m for m in ui.messages)
    visit('Daily schedule', **{'View date': date.today() + timedelta(days=1), 'Filter by status': 'Pending'})
    assert [(r['Pet'], r['Task']) for r in ui.tables[0]] == [('Mochi', 'Breakfast')]
    assert ui.session_state.owner.name == 'Alex'
