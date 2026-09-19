"""Database access for employees."""

import sqlite3
from dataclasses import replace

from shiftmanager.models import Employee

_COLUMNS = "id, name, position, phone, email, hourly_rate, color_tag, is_active"


def add(conn: sqlite3.Connection, employee: Employee) -> Employee:
    """Insert an employee and return a copy carrying its new id."""
    cursor = conn.execute(
        "INSERT INTO employees"
        " (name, position, phone, email, hourly_rate, color_tag, is_active)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        _values(employee),
    )
    conn.commit()
    return replace(employee, id=cursor.lastrowid)


def update(conn: sqlite3.Connection, employee: Employee) -> None:
    """Save changes to an already stored employee."""
    conn.execute(
        "UPDATE employees SET name = ?, position = ?, phone = ?, email = ?,"
        " hourly_rate = ?, color_tag = ?, is_active = ? WHERE id = ?",
        (*_values(employee), employee.id),
    )
    conn.commit()


def deactivate(conn: sqlite3.Connection, employee_id: int) -> None:
    """Retire an employee, keeping their past assignments intact."""
    conn.execute("UPDATE employees SET is_active = 0 WHERE id = ?", (employee_id,))
    conn.commit()


def get(conn: sqlite3.Connection, employee_id: int) -> Employee | None:
    """Return one employee, or None when no such employee exists."""
    row = conn.execute(
        f"SELECT {_COLUMNS} FROM employees WHERE id = ?", (employee_id,)
    ).fetchone()
    return row_to_employee(row) if row else None


def list_all(
    conn: sqlite3.Connection, include_inactive: bool = False
) -> list[Employee]:
    """Return employees by name, active ones only unless asked otherwise."""
    sql = f"SELECT {_COLUMNS} FROM employees"
    if not include_inactive:
        sql += " WHERE is_active = 1"
    rows = conn.execute(sql + " ORDER BY name").fetchall()
    return [row_to_employee(row) for row in rows]


def _values(employee: Employee) -> tuple:
    """The employee's column values, in the order the statements above use."""
    return (
        employee.name,
        employee.position,
        employee.phone,
        employee.email,
        employee.hourly_rate,
        employee.color_tag,
        int(employee.is_active),
    )


def row_to_employee(row: sqlite3.Row) -> Employee:
    """Build an Employee from a row selecting the employee columns above.

    Public so joins in other repositories can reuse it.
    """
    return Employee(
        id=row["id"],
        name=row["name"],
        position=row["position"],
        phone=row["phone"],
        email=row["email"],
        hourly_rate=row["hourly_rate"],
        color_tag=row["color_tag"],
        is_active=bool(row["is_active"]),
    )
