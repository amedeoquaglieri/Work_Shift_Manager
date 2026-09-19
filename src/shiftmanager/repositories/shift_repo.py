"""Database access for shifts and shift templates."""

import sqlite3
from dataclasses import replace

from shiftmanager.models import Shift, ShiftTemplate

_SHIFT_COLUMNS = "id, template_id, shift_date, start_time, end_time, notes"
_TEMPLATE_COLUMNS = "id, name, start_time, end_time"


def add(conn: sqlite3.Connection, shift: Shift) -> Shift:
    """Insert a shift and return a copy carrying its new id."""
    cursor = conn.execute(
        "INSERT INTO shifts (template_id, shift_date, start_time, end_time, notes)"
        " VALUES (?, ?, ?, ?, ?)",
        _shift_values(shift),
    )
    conn.commit()
    return replace(shift, id=cursor.lastrowid)


def update(conn: sqlite3.Connection, shift: Shift) -> None:
    """Save changes to an already stored shift."""
    conn.execute(
        "UPDATE shifts SET template_id = ?, shift_date = ?, start_time = ?,"
        " end_time = ?, notes = ? WHERE id = ?",
        (*_shift_values(shift), shift.id),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, shift_id: int) -> None:
    """Remove a shift along with its assignments."""
    conn.execute("DELETE FROM shifts WHERE id = ?", (shift_id,))
    conn.commit()


def get(conn: sqlite3.Connection, shift_id: int) -> Shift | None:
    """Return one shift, or None when no such shift exists."""
    row = conn.execute(
        f"SELECT {_SHIFT_COLUMNS} FROM shifts WHERE id = ?", (shift_id,)
    ).fetchone()
    return row_to_shift(row) if row else None


def list_between(
    conn: sqlite3.Connection, start_date: str, end_date: str
) -> list[Shift]:
    """Return shifts falling in the inclusive date range, in roster order."""
    rows = conn.execute(
        f"SELECT {_SHIFT_COLUMNS} FROM shifts WHERE shift_date BETWEEN ? AND ?"
        " ORDER BY shift_date, start_time",
        (start_date, end_date),
    ).fetchall()
    return [row_to_shift(row) for row in rows]


def add_template(
    conn: sqlite3.Connection, template: ShiftTemplate
) -> ShiftTemplate:
    """Insert a template and return a copy carrying its new id."""
    cursor = conn.execute(
        "INSERT INTO shift_templates (name, start_time, end_time) VALUES (?, ?, ?)",
        (template.name, template.start_time, template.end_time),
    )
    conn.commit()
    return replace(template, id=cursor.lastrowid)


def update_template(conn: sqlite3.Connection, template: ShiftTemplate) -> None:
    """Save changes to an already stored template."""
    conn.execute(
        "UPDATE shift_templates SET name = ?, start_time = ?, end_time = ?"
        " WHERE id = ?",
        (template.name, template.start_time, template.end_time, template.id),
    )
    conn.commit()


def delete_template(conn: sqlite3.Connection, template_id: int) -> None:
    """Remove a template, leaving shifts created from it untouched."""
    conn.execute(
        "UPDATE shifts SET template_id = NULL WHERE template_id = ?", (template_id,)
    )
    conn.execute("DELETE FROM shift_templates WHERE id = ?", (template_id,))
    conn.commit()


def get_template(
    conn: sqlite3.Connection, template_id: int
) -> ShiftTemplate | None:
    """Return one template, or None when no such template exists."""
    row = conn.execute(
        f"SELECT {_TEMPLATE_COLUMNS} FROM shift_templates WHERE id = ?",
        (template_id,),
    ).fetchone()
    return _to_template(row) if row else None


def list_templates(conn: sqlite3.Connection) -> list[ShiftTemplate]:
    """Return every template, ordered by start time."""
    rows = conn.execute(
        f"SELECT {_TEMPLATE_COLUMNS} FROM shift_templates ORDER BY start_time, name"
    ).fetchall()
    return [_to_template(row) for row in rows]


def _shift_values(shift: Shift) -> tuple:
    """The shift's column values, in the order the statements above use."""
    return (
        shift.template_id,
        shift.shift_date,
        shift.start_time,
        shift.end_time,
        shift.notes,
    )


def row_to_shift(row: sqlite3.Row) -> Shift:
    """Build a Shift from a row selecting the shift columns above.

    Public so joins in other repositories can reuse it.
    """
    return Shift(
        id=row["id"],
        template_id=row["template_id"],
        shift_date=row["shift_date"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        notes=row["notes"],
    )


def _to_template(row: sqlite3.Row) -> ShiftTemplate:
    return ShiftTemplate(
        id=row["id"],
        name=row["name"],
        start_time=row["start_time"],
        end_time=row["end_time"],
    )
