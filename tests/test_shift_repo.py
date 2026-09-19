"""Tests for the shift and shift template repository."""

from dataclasses import replace

from shiftmanager.models import Shift, ShiftTemplate
from shiftmanager.repositories import shift_repo


def a_shift(date="2026-09-21", start="09:00", end="17:00", **kwargs):
    return Shift(shift_date=date, start_time=start, end_time=end, **kwargs)


def test_add_returns_the_shift_with_an_id(conn):
    stored = shift_repo.add(conn, a_shift())

    assert stored.id is not None
    assert shift_repo.get(conn, stored.id) == stored


def test_get_returns_none_for_an_unknown_id(conn):
    assert shift_repo.get(conn, 999) is None


def test_update_saves_changes(conn):
    stored = shift_repo.add(conn, a_shift(notes="Opening"))

    shift_repo.update(conn, replace(stored, start_time="10:00", notes="Late open"))

    reloaded = shift_repo.get(conn, stored.id)
    assert reloaded.start_time == "10:00"
    assert reloaded.notes == "Late open"


def test_delete_removes_the_shift(conn):
    stored = shift_repo.add(conn, a_shift())

    shift_repo.delete(conn, stored.id)

    assert shift_repo.get(conn, stored.id) is None


def test_list_between_covers_both_end_dates(conn):
    for date in ("2026-09-20", "2026-09-21", "2026-09-27", "2026-09-28"):
        shift_repo.add(conn, a_shift(date=date))

    found = shift_repo.list_between(conn, "2026-09-21", "2026-09-27")

    assert [s.shift_date for s in found] == ["2026-09-21", "2026-09-27"]


def test_list_between_orders_by_date_then_start_time(conn):
    shift_repo.add(conn, a_shift(date="2026-09-22", start="09:00"))
    shift_repo.add(conn, a_shift(date="2026-09-21", start="17:00"))
    shift_repo.add(conn, a_shift(date="2026-09-21", start="06:00"))

    found = shift_repo.list_between(conn, "2026-09-21", "2026-09-22")

    assert [(s.shift_date, s.start_time) for s in found] == [
        ("2026-09-21", "06:00"),
        ("2026-09-21", "17:00"),
        ("2026-09-22", "09:00"),
    ]


def test_list_all_returns_every_shift_in_roster_order(conn):
    shift_repo.add(conn, a_shift(date="2026-09-28", start="09:00"))
    shift_repo.add(conn, a_shift(date="2026-09-21", start="17:00"))
    shift_repo.add(conn, a_shift(date="2026-09-21", start="06:00"))

    found = shift_repo.list_all(conn)

    assert [(s.shift_date, s.start_time) for s in found] == [
        ("2026-09-21", "06:00"),
        ("2026-09-21", "17:00"),
        ("2026-09-28", "09:00"),
    ]


def test_templates_round_trip(conn):
    stored = shift_repo.add_template(
        conn, ShiftTemplate(name="Morning", start_time="09:00", end_time="17:00")
    )

    assert shift_repo.get_template(conn, stored.id) == stored


def test_update_template_saves_changes(conn):
    stored = shift_repo.add_template(
        conn, ShiftTemplate(name="Morning", start_time="09:00", end_time="17:00")
    )

    shift_repo.update_template(conn, replace(stored, end_time="18:00"))

    assert shift_repo.get_template(conn, stored.id).end_time == "18:00"


def test_list_templates_is_ordered_by_start_time(conn):
    for name, start in (("Night", "22:00"), ("Morning", "06:00"), ("Late", "14:00")):
        shift_repo.add_template(
            conn, ShiftTemplate(name=name, start_time=start, end_time="23:59")
        )

    found = shift_repo.list_templates(conn)

    assert [t.name for t in found] == ["Morning", "Late", "Night"]


def test_deleting_a_template_keeps_its_shifts(conn):
    template = shift_repo.add_template(
        conn, ShiftTemplate(name="Morning", start_time="09:00", end_time="17:00")
    )
    shift = shift_repo.add(conn, a_shift(template_id=template.id))

    shift_repo.delete_template(conn, template.id)

    reloaded = shift_repo.get(conn, shift.id)
    assert reloaded is not None
    assert reloaded.template_id is None
    assert reloaded.start_time == "09:00"
