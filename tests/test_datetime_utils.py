"""Tests for the date and time helpers."""

from datetime import date, time

import pytest

from shiftmanager.utils import (
    add_days,
    duration_hours,
    format_date,
    format_weekday,
    month_bounds,
    parse_date,
    parse_time,
    today,
    week_bounds,
    week_dates,
    week_start,
)


def test_parse_and_format_round_trip():
    assert format_date(parse_date("2026-09-21")) == "2026-09-21"
    assert parse_date("2026-09-21") == date(2026, 9, 21)


def test_add_days_crosses_month_boundaries():
    assert add_days("2026-09-30", 1) == "2026-10-01"
    assert add_days("2026-10-01", -1) == "2026-09-30"


def test_week_start_finds_the_monday():
    # 2026-09-21 is a Monday, 2026-09-27 the Sunday that ends its week.
    assert week_start("2026-09-21") == "2026-09-21"
    assert week_start("2026-09-24") == "2026-09-21"
    assert week_start("2026-09-27") == "2026-09-21"


def test_week_start_crosses_a_month_boundary():
    assert week_start("2026-10-01") == "2026-09-28"


def test_week_bounds_runs_monday_to_sunday():
    assert week_bounds("2026-09-24") == ("2026-09-21", "2026-09-27")


def test_month_bounds_covers_the_whole_month():
    assert month_bounds("2026-09-15") == ("2026-09-01", "2026-09-30")
    assert month_bounds("2026-02-10") == ("2026-02-01", "2026-02-28")


def test_month_bounds_handles_a_leap_year():
    assert month_bounds("2028-02-10") == ("2028-02-01", "2028-02-29")


def test_week_dates_returns_seven_consecutive_days():
    dates = week_dates("2026-09-21")

    assert len(dates) == 7
    assert dates[0] == "2026-09-21"
    assert dates[-1] == "2026-09-27"


def test_format_weekday_names_the_day():
    assert format_weekday("2026-09-21").startswith("Mon")


def test_today_is_a_parseable_date():
    assert parse_date(today())


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
