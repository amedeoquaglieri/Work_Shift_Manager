"""Tests for the assignment repository."""

import pytest

from shiftmanager.models import Employee, Shift
from shiftmanager.repositories import assignment_repo, employee_repo, shift_repo


@pytest.fixture
def ada(conn):
    return employee_repo.add(conn, Employee(name="Ada"))


@pytest.fixture
def monday(conn):
    return shift_repo.add(
        conn, Shift(shift_date="2026-09-21", start_time="09:00", end_time="17:00")
    )


def test_add_returns_the_stored_assignment(conn, ada, monday):
    stored = assignment_repo.add(conn, monday.id, ada.id)

    assert stored.id is not None
    assert (stored.shift_id, stored.employee_id) == (monday.id, ada.id)


def test_list_for_shift_returns_only_that_shift(conn, ada, monday):
    mo = employee_repo.add(conn, Employee(name="Mo"))
    tuesday = shift_repo.add(
        conn, Shift(shift_date="2026-09-22", start_time="09:00", end_time="17:00")
    )
    assignment_repo.add(conn, monday.id, ada.id)
    assignment_repo.add(conn, monday.id, mo.id)
    assignment_repo.add(conn, tuesday.id, ada.id)

    found = assignment_repo.list_for_shift(conn, monday.id)

    assert sorted(a.employee_id for a in found) == sorted([ada.id, mo.id])


def test_remove_takes_the_employee_off_the_shift(conn, ada, monday):
    assignment_repo.add(conn, monday.id, ada.id)

    assignment_repo.remove(conn, monday.id, ada.id)

    assert assignment_repo.list_for_shift(conn, monday.id) == []


def test_shifts_for_employee_returns_only_their_shifts_in_range(conn, ada, monday):
    mo = employee_repo.add(conn, Employee(name="Mo"))
    sunday = shift_repo.add(
        conn, Shift(shift_date="2026-09-20", start_time="09:00", end_time="17:00")
    )
    tuesday = shift_repo.add(
        conn, Shift(shift_date="2026-09-22", start_time="09:00", end_time="17:00")
    )
    assignment_repo.add(conn, sunday.id, ada.id)
    assignment_repo.add(conn, monday.id, ada.id)
    assignment_repo.add(conn, tuesday.id, mo.id)

    found = assignment_repo.shifts_for_employee(
        conn, ada.id, "2026-09-21", "2026-09-27"
    )

    assert [s.id for s in found] == [monday.id]


def test_shifts_for_employee_returns_whole_shifts(conn, ada, monday):
    assignment_repo.add(conn, monday.id, ada.id)

    found = assignment_repo.shifts_for_employee(
        conn, ada.id, "2026-09-21", "2026-09-21"
    )

    assert found == [monday]


def test_shifts_for_employee_is_empty_when_unassigned(conn, ada):
    assert (
        assignment_repo.shifts_for_employee(conn, ada.id, "2026-09-21", "2026-09-27")
        == []
    )
