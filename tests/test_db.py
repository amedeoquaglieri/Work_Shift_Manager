"""Tests for connection setup and schema creation."""

import sqlite3

import pytest

from shiftmanager.db import connect, create_schema

EXPECTED_TABLES = {"employees", "shift_templates", "shifts", "assignments"}


def table_names(connection):
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {row["name"] for row in rows}


def test_connect_creates_all_tables(conn):
    assert EXPECTED_TABLES <= table_names(conn)


def test_rows_are_accessible_by_column_name(conn):
    conn.execute("INSERT INTO employees (name) VALUES ('Ada')")
    row = conn.execute("SELECT name, is_active FROM employees").fetchone()
    assert row["name"] == "Ada"
    assert row["is_active"] == 1


def test_create_schema_is_idempotent(conn):
    conn.execute("INSERT INTO employees (name) VALUES ('Ada')")
    conn.commit()
    create_schema(conn)
    assert EXPECTED_TABLES <= table_names(conn)
    assert conn.execute("SELECT COUNT(*) AS n FROM employees").fetchone()["n"] == 1


def test_foreign_keys_are_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO assignments (shift_id, employee_id) VALUES (999, 999)"
        )


def test_deleting_a_shift_cascades_to_its_assignments(conn):
    conn.execute("INSERT INTO employees (name) VALUES ('Ada')")
    conn.execute(
        "INSERT INTO shifts (shift_date, start_time, end_time)"
        " VALUES ('2026-09-21', '09:00', '17:00')"
    )
    conn.execute("INSERT INTO assignments (shift_id, employee_id) VALUES (1, 1)")

    conn.execute("DELETE FROM shifts WHERE id = 1")

    assert conn.execute("SELECT COUNT(*) AS n FROM assignments").fetchone()["n"] == 0


def test_an_employee_cannot_be_assigned_to_the_same_shift_twice(conn):
    conn.execute("INSERT INTO employees (name) VALUES ('Ada')")
    conn.execute(
        "INSERT INTO shifts (shift_date, start_time, end_time)"
        " VALUES ('2026-09-21', '09:00', '17:00')"
    )
    conn.execute("INSERT INTO assignments (shift_id, employee_id) VALUES (1, 1)")

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO assignments (shift_id, employee_id) VALUES (1, 1)")


def test_connect_creates_the_database_file(tmp_path):
    db_path = tmp_path / "nested" / "shifts.db"

    connection = connect(db_path)
    connection.close()

    assert db_path.exists()
