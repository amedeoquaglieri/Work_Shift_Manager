"""Tests for the domain model defaults."""

from shiftmanager.models import Assignment, Employee, Shift, ShiftTemplate


def test_a_new_employee_is_active_and_unsaved():
    employee = Employee(name="Ada")
    assert employee.is_active is True
    assert employee.id is None
    assert employee.hourly_rate is None


def test_a_shift_needs_only_a_date_and_times():
    shift = Shift(shift_date="2026-09-21", start_time="09:00", end_time="17:00")
    assert shift.template_id is None
    assert shift.notes is None
    assert shift.id is None


def test_a_template_carries_its_times():
    template = ShiftTemplate(name="Morning", start_time="09:00", end_time="17:00")
    assert (template.start_time, template.end_time) == ("09:00", "17:00")


def test_an_assignment_links_a_shift_to_an_employee():
    assignment = Assignment(shift_id=1, employee_id=2)
    assert (assignment.shift_id, assignment.employee_id) == (1, 2)
    assert assignment.id is None
