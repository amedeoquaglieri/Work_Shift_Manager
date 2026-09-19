"""Application entry point.

Opens the database and launches the Tk main window. The GUI is added in a
later build step; for now this only sets up the database.
"""

from shiftmanager.db import DEFAULT_DB_PATH, connect


def main() -> None:
    """Start the Work Shift Manager application."""
    conn = connect()
    conn.close()
    print(f"Work Shift Manager: database ready at {DEFAULT_DB_PATH}.")


if __name__ == "__main__":
    main()
