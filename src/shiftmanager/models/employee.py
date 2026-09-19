"""Employee domain model."""

from dataclasses import dataclass


@dataclass
class Employee:
    """A member of staff who can be assigned to shifts.

    ``id`` is None until the employee has been saved. Employees are
    deactivated rather than deleted, so ``is_active`` decides whether they
    appear in assignment pickers.
    """

    name: str
    position: str | None = None
    phone: str | None = None
    email: str | None = None
    hourly_rate: float | None = None
    color_tag: str | None = None
    is_active: bool = True
    id: int | None = None
