"""Assignment domain model."""

from dataclasses import dataclass


@dataclass
class Assignment:
    """A link putting one employee on one shift."""

    shift_id: int
    employee_id: int
    id: int | None = None
