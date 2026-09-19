# Work Shift Manager

A Tkinter desktop app for managing employee work shifts: maintain employees,
create shifts, assign staff to them, view a weekly roster, and report on
scheduled hours. Runs as a single local app with no login, storing everything
in a local SQLite file.

**Status:** v1 complete. See [`planning/PLAN.md`](planning/PLAN.md) for the
design and the stretch goals deliberately left out.

## Requirements

- Python 3.11+ (with `tkinter`, included in most distributions)
- [`uv`](https://docs.astral.sh/uv/)

No third-party runtime dependencies — the app uses the standard library only.

## Setup

```bash
uv sync
```

## Usage

```bash
uv run python -m shiftmanager.main
```

The database is created at `data/shifts.db` on first run.

## Using it

The sidebar switches between three screens.

**Roster** shows one week as seven day columns. The `+` in a day header
creates a shift on that day. Click a shift card to choose who works it;
right-click for edit and delete. `< Previous`, `Today` and `Next >` move
between weeks, and `Manage templates` maintains the reusable shift times.

**Employees** lists staff with search and a `Show inactive` toggle. Staff
are deactivated rather than deleted, so their past shifts survive; the
Active tick box in the edit dialog brings someone back.

**Reports** totals scheduled hours per employee over a date range, with
`This week` and `This month` shortcuts, an employee filter, and CSV export.

Assigning someone to a shift overlapping one they already work is flagged
beside their name and confirmed again on save. A shift ending earlier than
it starts, such as 22:00 to 06:00, runs into the next day and counts its
hours against the day it starts on.

## Features

- **Employees** — add, edit, and deactivate staff, with position, contact
  details, optional hourly rate, and a colour tag shown on the roster.
- **Shifts** — reusable templates plus individual shifts on specific dates
  with custom times and notes.
- **Assignments** — several employees per shift, with double-booking
  warnings when a shift overlaps one they already work.
- **Weekly roster** — Monday–Sunday grid of shifts and who covers them,
  with week navigation.
- **Reports** — scheduled hours per employee over a date range, exportable
  as CSV.

## Testing

```bash
uv run pytest
```

Tests cover the repositories, scheduling conflict detection and report
totals against an in-memory database, plus a pass that builds every window
and dialog. Those construction tests skip themselves where no display is
available.

Behaviour is still worth walking through by hand after changing the GUI:

1. Add an employee, then edit and deactivate one.
2. Create a template, then a shift from it and one with custom times.
3. Assign two employees to a shift; confirm an overlapping assignment warns
   and that declining the warning leaves nothing assigned.
4. Check the shift and its staff appear on the correct roster day.
5. Navigate to the previous and next week, then back to today.
6. Run an hours report for the week and export it as CSV.

## Project Layout

```
src/shiftmanager/
├── db/            # connection and schema
├── models/        # dataclasses
├── repositories/  # all SQL
├── services/      # scheduling rules and reporting
├── gui/           # Tk views and dialogs
└── utils/         # date and time helpers
```

Dependencies run one way: `gui` → `services` → `repositories` → `db`.

## License

[MIT](LICENSE)
