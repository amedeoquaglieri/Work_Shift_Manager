"""Conversions between the app's date and time strings and datetime objects.

Dates are ``"YYYY-MM-DD"`` and times are ``"HH:MM"`` everywhere else in the
app. This module is the only place that turns them into datetime objects.
"""

from datetime import date, datetime, time, timedelta

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


def parse_date(date_str: str) -> date:
    """Read a ``"YYYY-MM-DD"`` string."""
    return datetime.strptime(date_str, DATE_FORMAT).date()


def format_date(value: date) -> str:
    """Write a date as ``"YYYY-MM-DD"``."""
    return value.strftime(DATE_FORMAT)


def today() -> str:
    """Today's date as ``"YYYY-MM-DD"``."""
    return format_date(date.today())


def week_start(date_str: str) -> str:
    """The Monday of the week containing the given date."""
    value = parse_date(date_str)
    return format_date(value - timedelta(days=value.weekday()))


def week_dates(start_date: str) -> list[str]:
    """Seven consecutive dates beginning at the given one."""
    return [add_days(start_date, offset) for offset in range(7)]


def format_weekday(date_str: str) -> str:
    """A short day label such as ``"Mon 21 Sep"``."""
    return parse_date(date_str).strftime("%a %d %b")


def parse_time(time_str: str) -> time:
    """Read an ``"HH:MM"`` string, raising ValueError when it is malformed."""
    return datetime.strptime(time_str, TIME_FORMAT).time()


def add_days(date_str: str, days: int) -> str:
    """Shift a date string by a number of days."""
    return format_date(parse_date(date_str) + timedelta(days=days))


def shift_span(
    shift_date: str, start_time: str, end_time: str
) -> tuple[datetime, datetime]:
    """Return the moments a shift starts and ends.

    An ``end_time`` earlier than ``start_time`` means the shift runs past
    midnight, so it ends on the following day.
    """
    start = _at(shift_date, start_time)
    end = _at(shift_date, end_time)
    if end < start:
        end += timedelta(days=1)
    return start, end


def duration_hours(shift_date: str, start_time: str, end_time: str) -> float:
    """How many hours a shift lasts, rounded to two decimals."""
    start, end = shift_span(shift_date, start_time, end_time)
    return round((end - start).total_seconds() / 3600, 2)


def _at(date_str: str, time_str: str) -> datetime:
    return datetime.strptime(
        f"{date_str} {time_str}", f"{DATE_FORMAT} {TIME_FORMAT}"
    )
