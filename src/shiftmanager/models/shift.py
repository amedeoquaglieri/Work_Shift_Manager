"""Shift and shift template domain models."""

from dataclasses import dataclass


@dataclass
class ShiftTemplate:
    """A reusable set of shift times, such as "Morning" 09:00 to 17:00.

    Times are ``"HH:MM"`` strings.
    """

    name: str
    start_time: str
    end_time: str
    id: int | None = None


@dataclass
class Shift:
    """A shift on a specific day that employees can be assigned to.

    ``shift_date`` is a ``"YYYY-MM-DD"`` string and the times are ``"HH:MM"``
    strings. An ``end_time`` earlier than ``start_time`` means the shift runs
    past midnight into the next day. ``template_id`` records the template the
    shift was created from, if any; the times are always stored on the shift
    itself so later template edits do not rewrite past shifts.
    """

    shift_date: str
    start_time: str
    end_time: str
    template_id: int | None = None
    notes: str | None = None
    id: int | None = None
