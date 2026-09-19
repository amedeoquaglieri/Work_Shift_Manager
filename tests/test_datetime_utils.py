"""Tests for the date and time helpers."""

from datetime import date, time

import pytest

from shiftmanager.utils import (
    add_days,
    duration_hours,
    format_date,
    parse_date,
    parse_time,
)


def test_parse_and_format_round_trip():
    assert format_date(parse_date("2026-09-21")) == "2026-09-21"
    assert parse_date("2026-09-21") == date(2026, 9, 21)


def test_add_days_crosses_month_boundaries():
    assert add_days("2026-09-30", 1) == "2026-10-01"
    assert add_days("2026-10-01", -1) == "2026-09-30"


def test_parse_time_reads_a_clock_time():
    assert parse_time("09:30") == time(9, 30)


@pytest.mark.parametrize("bad", ["", "9:30am", "25:00", "09-30", "0930"])
def test_parse_time_rejects_malformed_input(bad):
    with pytest.raises(ValueError):
        parse_time(bad)


def test_duration_of_a_normal_shift():
    assert duration_hours("2026-09-21", "09:00", "17:00") == 8.0


def test_duration_handles_half_hours():
    assert duration_hours("2026-09-21", "09:15", "17:45") == 8.5


def test_duration_of_an_overnight_shift_runs_into_the_next_day():
    assert duration_hours("2026-09-21", "22:00", "06:00") == 8.0


def test_equal_times_are_a_zero_length_shift():
    assert duration_hours("2026-09-21", "09:00", "09:00") == 0.0
