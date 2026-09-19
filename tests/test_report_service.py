"""Tests for the hours report and its CSV export."""

import csv

import pytest

from shiftmanager.models import Employee, Shift
from shiftmanager.repositories import assignment_repo, employee_repo, shift_repo
from shiftmanager.services import report_service

WEEK_START = "2026-09-21"
WEEK_END = "2026-09-27"


@pytest.fixture
def ada(conn):
    return employee_repo.add(conn, Employee(name="Ada", position="Barista"))


def book(conn, employee, date=WEEK_START, start="09:00", end="17:00"):
    shift = shift_repo.add(
        conn, Shift(shift_date=date, start_time=start, end_time=end)
    )
    assignment_repo.add(conn, shift.id, employee.id)
    return shift


def rows_by_name(conn, start=WEEK_START, end=WEEK_END):
    return {
        row.employee.name: row
        for row in report_service.hours_by_employee(conn, start, end)
    }


def test_hours_are_summed_across_shifts(conn, ada):
    book(conn, ada, date="2026-09-21", start="09:00", end="17:00")
    book(conn, ada, date="2026-09-23", start="09:00", end="12:30")

    row = rows_by_name(conn)["Ada"]

    assert row.shift_count == 2
    assert row.hours == 11.5


def test_overnight_hours_count_towards_the_starting_day(conn, ada):
    book(conn, ada, date="2026-09-27", start="22:00", end="06:00")

    assert rows_by_name(conn)["Ada"].hours == 8.0


def test_shifts_outside_the_range_are_excluded(conn, ada):
    book(conn, ada, date="2026-09-20")
    book(conn, ada, date="2026-09-28")

    row = rows_by_name(conn)["Ada"]

    assert row.shift_count == 0
    assert row.hours == 0.0


def test_an_active_employee_with_no_shifts_still_appears(conn, ada):
    assert rows_by_name(conn)["Ada"].hours == 0.0


def test_hours_are_always_a_float(conn, ada):
    """Zero hours must not come back as an int, or the CSV column mixes types."""
    assert isinstance(rows_by_name(conn)["Ada"].hours, float)

    book(conn, ada)

    assert isinstance(rows_by_name(conn)["Ada"].hours, float)


def test_a_deactivated_employee_with_no_shifts_is_dropped(conn, ada):
    employee_repo.deactivate(conn, ada.id)

    assert "Ada" not in rows_by_name(conn)


def test_a_deactivated_employee_who_worked_still_appears(conn, ada):
    book(conn, ada)
    employee_repo.deactivate(conn, ada.id)

    assert rows_by_name(conn)["Ada"].hours == 8.0


def test_each_employee_gets_their_own_hours(conn, ada):
    mo = employee_repo.add(conn, Employee(name="Mo"))
    book(conn, ada, start="09:00", end="17:00")
    book(conn, mo, start="17:00", end="22:00")

    rows = rows_by_name(conn)

    assert rows["Ada"].hours == 8.0
    assert rows["Mo"].hours == 5.0


def test_export_csv_writes_a_header_and_a_row_per_employee(conn, ada, tmp_path):
    book(conn, ada)
    path = tmp_path / "reports" / "hours.csv"

    rows = report_service.hours_by_employee(conn, WEEK_START, WEEK_END)
    report_service.export_csv(rows, path)

    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == list(report_service.CSV_HEADER)
    assert rows[1] == ["Ada", "Barista", "1", "8.0"]
