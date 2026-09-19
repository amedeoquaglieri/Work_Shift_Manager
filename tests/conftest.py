"""Shared test fixtures."""

import pytest

from shiftmanager.db import IN_MEMORY, connect


@pytest.fixture
def conn():
    """An empty in-memory database with the schema applied."""
    connection = connect(IN_MEMORY)
    yield connection
    connection.close()
