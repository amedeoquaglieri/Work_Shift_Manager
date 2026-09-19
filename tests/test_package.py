"""Smoke test confirming the package is importable and installed."""

import shiftmanager
from shiftmanager.main import main


def test_package_exposes_entry_point():
    assert shiftmanager.__doc__
    assert callable(main)
