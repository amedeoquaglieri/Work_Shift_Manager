"""Rules for putting employees on shifts without double-booking them."""

import sqlite3

from shiftmanager.models import Assignment, Shift
from shiftmanager.repositories import assignment_repo, shift_repo
from shiftmanager.utils import add_days, shift_span


class ConflictError(Exception):
    """Raised when an assignment would double-book an employee."""

    def __init__(self, conflicts: list[Shift]):
        self.conflicts = conflicts
        super().__init__(f"employee is already on {len(conflicts)} overlapping shift(s)")


def find_conflicts(
    conn: sqlite3.Connection, employee_id: int, shift: Shift
) -> list[Shift]:
    """Return the employee's existing shifts that overlap the given shift.

    Shifts on the neighbouring days are checked too, since a shift running
    past midnight can overlap one starting early the next morning.
    """
    existing = assignment_repo.shifts_for_employee(
        conn,
        employee_id,
        add_days(shift.shift_date, -1),
        add_days(shift.shift_date, 1),
    )
    return [
        other
        for other in existing
        if other.id != shift.id and _overlaps(shift, other)
    ]


def assign(
    conn: sqlite3.Connection, shift_id: int, employee_id: int, force: bool = False
) -> Assignment:
    """Put an employee on a shift.

    Raises ConflictError when the shift overlaps one they are already on,
    unless ``force`` is set to accept the clash.
    """
    if not force:
        shift = shift_repo.get(conn, shift_id)
        conflicts = find_conflicts(conn, employee_id, shift)
        if conflicts:
            raise ConflictError(conflicts)
    return assignment_repo.add(conn, shift_id, employee_id)


def _overlaps(one: Shift, other: Shift) -> bool:
    """Whether two shifts share any time. Touching end to end does not count."""
    one_start, one_end = shift_span(one.shift_date, one.start_time, one.end_time)
    other_start, other_end = shift_span(
        other.shift_date, other.start_time, other.end_time
    )
    return one_start < other_end and other_start < one_end
