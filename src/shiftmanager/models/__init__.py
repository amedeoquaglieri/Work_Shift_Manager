"""Domain models: plain dataclasses with no database or GUI knowledge."""

from shiftmanager.models.assignment import Assignment
from shiftmanager.models.employee import Employee
from shiftmanager.models.shift import Shift, ShiftTemplate

__all__ = ["Assignment", "Employee", "Shift", "ShiftTemplate"]
