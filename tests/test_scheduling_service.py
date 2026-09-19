"""Tests for conflict detection and assignment."""

import pytest

from shiftmanager.models import Employee, Shift
from shiftmanager.repositories import assignment_repo, employee_repo, shift_repo
from shiftmanager.services import scheduling_service
from shiftmanager.services.scheduling_service import ConflictError

MONDAY = "2026-09-21"
TUESDAY = "2026-09-22"


@pytest.fixture
def ada(conn):
    return employee_repo.add(conn, Employee(name="Ada"))


def make_shift(conn, date=MONDAY, start="09:00", end="17:00"):
    return shift_repo.add(
        conn, Shift(shift_date=date, start_time=start, end_time=end)
    )


def book(conn, employee, **kwargs):
    """Put the employee on a new shift and return that shift."""
    shift = make_shift(conn, **kwargs)
    assignment_repo.add(conn, shift.id, employee.id)
    return shift


def test_no_conflict_when_the_employee_is_free(conn, ada):
    shift = make_shift(conn)

    assert scheduling_service.find_conflicts(conn, ada.id, shift) == []


def test_overlapping_shifts_conflict(conn, ada):
    booked = book(conn, ada, start="09:00", end="17:00")
    proposed = make_shift(conn, start="16:00", end="20:00")

    assert scheduling_service.find_conflicts(conn, ada.id, proposed) == [booked]


def test_back_to_back_shifts_do_not_conflict(conn, ada):
    book(conn, ada, start="09:00", end="17:00")
    proposed = make_shift(conn, start="17:00", end="22:00")

    assert scheduling_service.find_conflicts(conn, ada.id, proposed) == []


def test_a_shift_contained_in_another_conflicts(conn, ada):
    booked = book(conn, ada, start="09:00", end="17:00")
    proposed = make_shift(conn, start="11:00", end="13:00")

    assert scheduling_service.find_conflicts(conn, ada.id, proposed) == [booked]


def test_identical_shifts_on_different_days_do_not_conflict(conn, ada):
    book(conn, ada, date=MONDAY)
    proposed = make_shift(conn, date=TUESDAY)

    assert scheduling_service.find_conflicts(conn, ada.id, proposed) == []


def test_an_overnight_shift_conflicts_with_the_next_morning(conn, ada):
    booked = book(conn, ada, date=MONDAY, start="22:00", end="06:00")
    proposed = make_shift(conn, date=TUESDAY, start="05:00", end="09:00")

    assert scheduling_service.find_conflicts(conn, ada.id, proposed) == [booked]


def test_an_overnight_shift_clears_the_next_afternoon(conn, ada):
    book(conn, ada, date=MONDAY, start="22:00", end="06:00")
    proposed = make_shift(conn, date=TUESDAY, start="14:00", end="18:00")

    assert scheduling_service.find_conflicts(conn, ada.id, proposed) == []


def test_another_employees_shift_is_not_a_conflict(conn, ada):
    mo = employee_repo.add(conn, Employee(name="Mo"))
    book(conn, mo, start="09:00", end="17:00")
    proposed = make_shift(conn, start="10:00", end="14:00")

    assert scheduling_service.find_conflicts(conn, ada.id, proposed) == []


def test_a_shift_does_not_conflict_with_itself(conn, ada):
    booked = book(conn, ada, start="09:00", end="17:00")

    assert scheduling_service.find_conflicts(conn, ada.id, booked) == []


def test_assign_stores_the_assignment(conn, ada):
    shift = make_shift(conn)

    stored = scheduling_service.assign(conn, shift.id, ada.id)

    assert stored.id is not None
    assert assignment_repo.list_for_shift(conn, shift.id) == [stored]


def test_assign_refuses_to_double_book(conn, ada):
    booked = book(conn, ada, start="09:00", end="17:00")
    clashing = make_shift(conn, start="16:00", end="20:00")

    with pytest.raises(ConflictError) as error:
        scheduling_service.assign(conn, clashing.id, ada.id)

    assert error.value.conflicts == [booked]
    assert assignment_repo.list_for_shift(conn, clashing.id) == []


def test_assign_with_force_accepts_the_clash(conn, ada):
    book(conn, ada, start="09:00", end="17:00")
    clashing = make_shift(conn, start="16:00", end="20:00")

    stored = scheduling_service.assign(conn, clashing.id, ada.id, force=True)

    assert assignment_repo.list_for_shift(conn, clashing.id) == [stored]
