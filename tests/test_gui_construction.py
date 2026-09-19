"""Construction tests for the Tk views and dialogs.

These catch mistakes that only show up when a widget is built or torn down,
such as naming an attribute something tkinter already uses internally. They
skip themselves where no display is available.
"""

import pytest

tkinter = pytest.importorskip("tkinter")

from shiftmanager.db import IN_MEMORY, connect  # noqa: E402
from shiftmanager.gui import App  # noqa: E402
from shiftmanager.gui.assignment_dialog import AssignmentDialog  # noqa: E402
from shiftmanager.gui.employee_dialog import EmployeeDialog  # noqa: E402
from shiftmanager.gui.shift_dialog import ShiftDialog  # noqa: E402
from shiftmanager.gui.template_dialog import TemplateDialog  # noqa: E402
from shiftmanager.gui.template_manager import TemplateManager  # noqa: E402
from shiftmanager.models import Employee, Shift, ShiftTemplate  # noqa: E402
from shiftmanager.repositories import (  # noqa: E402
    assignment_repo,
    employee_repo,
    shift_repo,
)
from shiftmanager.utils import today  # noqa: E402


@pytest.fixture(scope="module")
def app():
    """One hidden main window shared by the whole module.

    Tk does not reliably start a second root in the same process, so these
    tests build it once rather than per test.
    """
    connection = connect(IN_MEMORY)
    try:
        window = App(connection)
    except tkinter.TclError as error:
        pytest.skip(f"no usable Tk display: {error}")
    window.withdraw()
    yield window
    window.destroy()
    connection.close()


def test_the_window_builds_every_view(app):
    assert set(app._views) == {"Roster", "Employees", "Reports"}


def test_employee_dialog_builds_and_closes(app):
    EmployeeDialog(app, "Add Employee").destroy()


def test_employee_dialog_builds_from_an_existing_employee(app):
    employee = Employee(name="Ada", is_active=False, id=1)
    EmployeeDialog(app, "Edit Employee", employee=employee).destroy()


def test_shift_dialog_builds_and_closes(app):
    ShiftDialog(app, app.conn, "New Shift").destroy()


def test_shift_dialog_builds_from_an_existing_shift(app):
    shift = Shift(shift_date="2026-09-21", start_time="09:00", end_time="17:00", id=1)
    ShiftDialog(app, app.conn, "Edit Shift", shift=shift).destroy()


def test_template_dialog_builds_and_closes(app):
    TemplateDialog(app, "Add Template").destroy()


def test_template_dialog_builds_from_an_existing_template(app):
    template = ShiftTemplate(name="Morning", start_time="09:00", end_time="17:00", id=1)
    TemplateDialog(app, "Edit Template", template=template).destroy()


def test_template_manager_builds_and_closes(app):
    TemplateManager(app, app.conn).destroy()


def test_the_roster_draws_seven_days(app):
    roster = app._views["Roster"]

    roster.refresh()

    assert len(roster._grid.winfo_children()) == 7


def test_the_roster_draws_a_staffed_shift(app):
    shift = shift_repo.add(
        app.conn, Shift(shift_date=today(), start_time="09:00", end_time="17:00")
    )
    employee = employee_repo.add(app.conn, Employee(name="Rostered", color_tag="#3366cc"))
    assignment_repo.add(app.conn, shift.id, employee.id)

    roster = app._views["Roster"]
    roster.refresh()

    cards = [
        child
        for column in roster._grid.winfo_children()
        for child in column.winfo_children()
        if child.winfo_class() == "TLabelframe"
    ]
    assert any(card.cget("text") == "09:00 - 17:00" for card in cards)


def test_the_roster_survives_an_unusable_colour_tag(app):
    """A bad colour in the database must not stop the window opening."""
    shift = shift_repo.add(
        app.conn, Shift(shift_date=today(), start_time="07:00", end_time="08:00")
    )
    employee = employee_repo.add(
        app.conn, Employee(name="Bad Colour", color_tag="zzz")
    )
    assignment_repo.add(app.conn, shift.id, employee.id)

    app._views["Roster"].refresh()


def test_the_report_view_runs_for_the_current_week(app):
    report = app._views["Reports"]

    report.refresh()

    assert "hours scheduled" in report._total.get()


def test_assignment_dialog_builds_and_closes(app):
    shift = shift_repo.add(
        app.conn, Shift(shift_date="2026-09-21", start_time="09:00", end_time="17:00")
    )
    employee_repo.add(app.conn, Employee(name="Ada"))

    AssignmentDialog(app, app.conn, shift).destroy()


def test_assignment_dialog_builds_with_no_employees(app):
    shift = shift_repo.add(
        app.conn, Shift(shift_date="2026-09-22", start_time="09:00", end_time="17:00")
    )

    AssignmentDialog(app, app.conn, shift).destroy()
