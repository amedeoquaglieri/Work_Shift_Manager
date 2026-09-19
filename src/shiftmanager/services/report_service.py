"""Scheduled hours summaries and their CSV export."""

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from shiftmanager.models import Employee
from shiftmanager.repositories import assignment_repo, employee_repo
from shiftmanager.utils import duration_hours

CSV_HEADER = ("Employee", "Position", "Shifts", "Hours")


@dataclass
class EmployeeHours:
    """One row of the hours report."""

    employee: Employee
    shift_count: int
    hours: float


def hours_by_employee(
    conn: sqlite3.Connection, start_date: str, end_date: str
) -> list[EmployeeHours]:
    """Summarise scheduled hours per employee over an inclusive date range.

    Active employees appear even with no shifts, so gaps in the roster are
    visible. Deactivated employees appear only if they worked in the range.
    A shift counts towards the day it starts on, including overnight ones.
    """
    rows = []
    for employee in employee_repo.list_all(conn, include_inactive=True):
        shifts = assignment_repo.shifts_for_employee(
            conn, employee.id, start_date, end_date
        )
        if not shifts and not employee.is_active:
            continue
        hours = sum(
            (duration_hours(s.shift_date, s.start_time, s.end_time) for s in shifts),
            0.0,
        )
        rows.append(
            EmployeeHours(
                employee=employee, shift_count=len(shifts), hours=round(hours, 2)
            )
        )
    return rows


def export_csv(rows: list[EmployeeHours], path: str | Path) -> None:
    """Write an hours report to a CSV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        for row in rows:
            writer.writerow(
                [
                    row.employee.name,
                    row.employee.position or "",
                    row.shift_count,
                    row.hours,
                ]
            )
