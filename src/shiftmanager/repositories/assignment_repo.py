"""Database access for assignments of employees to shifts."""

import sqlite3

from shiftmanager.models import Assignment, Employee, Shift
from shiftmanager.repositories.employee_repo import row_to_employee
from shiftmanager.repositories.shift_repo import row_to_shift


def add(conn: sqlite3.Connection, shift_id: int, employee_id: int) -> Assignment:
    """Put an employee on a shift and return the stored assignment."""
    cursor = conn.execute(
        "INSERT INTO assignments (shift_id, employee_id) VALUES (?, ?)",
        (shift_id, employee_id),
    )
    conn.commit()
    return Assignment(id=cursor.lastrowid, shift_id=shift_id, employee_id=employee_id)


def remove(conn: sqlite3.Connection, shift_id: int, employee_id: int) -> None:
    """Take an employee off a shift."""
    conn.execute(
        "DELETE FROM assignments WHERE shift_id = ? AND employee_id = ?",
        (shift_id, employee_id),
    )
    conn.commit()


def list_for_shift(conn: sqlite3.Connection, shift_id: int) -> list[Assignment]:
    """Return the assignments on one shift."""
    rows = conn.execute(
        "SELECT id, shift_id, employee_id FROM assignments WHERE shift_id = ?",
        (shift_id,),
    ).fetchall()
    return [
        Assignment(
            id=row["id"], shift_id=row["shift_id"], employee_id=row["employee_id"]
        )
        for row in rows
    ]


def employees_for_shift(conn: sqlite3.Connection, shift_id: int) -> list[Employee]:
    """Return the employees working a shift, by name.

    Includes deactivated employees, so someone retired after being rostered
    still shows on the shift and can be taken off it.
    """
    rows = conn.execute(
        "SELECT e.id, e.name, e.position, e.phone, e.email, e.hourly_rate,"
        " e.color_tag, e.is_active FROM employees e"
        " JOIN assignments a ON a.employee_id = e.id"
        " WHERE a.shift_id = ? ORDER BY e.name",
        (shift_id,),
    ).fetchall()
    return [row_to_employee(row) for row in rows]


def shifts_for_employee(
    conn: sqlite3.Connection,
    employee_id: int,
    start_date: str,
    end_date: str,
) -> list[Shift]:
    """Return the shifts an employee is on within the inclusive date range.

    Used for conflict checks and for summing an employee's scheduled hours.
    """
    rows = conn.execute(
        "SELECT s.id, s.template_id, s.shift_date, s.start_time, s.end_time, s.notes"
        " FROM shifts s JOIN assignments a ON a.shift_id = s.id"
        " WHERE a.employee_id = ? AND s.shift_date BETWEEN ? AND ?"
        " ORDER BY s.shift_date, s.start_time",
        (employee_id, start_date, end_date),
    ).fetchall()
    return [row_to_shift(row) for row in rows]
