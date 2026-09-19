"""Application entry point: open the database, then run the main window."""

from shiftmanager.db import connect
from shiftmanager.gui import App


def main() -> None:
    """Start the Work Shift Manager application."""
    conn = connect()
    try:
        App(conn).mainloop()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
