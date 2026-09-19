"""Tests for the employee repository."""

from dataclasses import replace

from shiftmanager.models import Employee
from shiftmanager.repositories import employee_repo


def test_add_returns_the_employee_with_an_id(conn):
    stored = employee_repo.add(conn, Employee(name="Ada", position="Barista"))

    assert stored.id is not None
    assert stored.name == "Ada"


def test_add_leaves_the_given_employee_untouched(conn):
    employee = Employee(name="Ada")

    employee_repo.add(conn, employee)

    assert employee.id is None


def test_get_round_trips_every_field(conn):
    stored = employee_repo.add(
        conn,
        Employee(
            name="Ada",
            position="Barista",
            phone="555-0100",
            email="ada@example.com",
            hourly_rate=14.5,
            color_tag="#3366cc",
        ),
    )

    assert employee_repo.get(conn, stored.id) == stored


def test_get_returns_none_for_an_unknown_id(conn):
    assert employee_repo.get(conn, 999) is None


def test_update_saves_changes(conn):
    stored = employee_repo.add(conn, Employee(name="Ada", hourly_rate=14.5))

    employee_repo.update(conn, replace(stored, name="Ada L", hourly_rate=16.0))

    reloaded = employee_repo.get(conn, stored.id)
    assert reloaded.name == "Ada L"
    assert reloaded.hourly_rate == 16.0


def test_list_all_is_ordered_by_name(conn):
    for name in ("Zoe", "Ada", "Mo"):
        employee_repo.add(conn, Employee(name=name))

    assert [e.name for e in employee_repo.list_all(conn)] == ["Ada", "Mo", "Zoe"]


def test_deactivated_employees_are_hidden_unless_asked_for(conn):
    stored = employee_repo.add(conn, Employee(name="Ada"))

    employee_repo.deactivate(conn, stored.id)

    assert employee_repo.list_all(conn) == []
    remaining = employee_repo.list_all(conn, include_inactive=True)
    assert [e.name for e in remaining] == ["Ada"]
    assert remaining[0].is_active is False


def test_is_active_survives_the_round_trip_as_a_bool(conn):
    stored = employee_repo.add(conn, Employee(name="Ada", is_active=False))

    assert employee_repo.get(conn, stored.id).is_active is False
