# Work Shift Manager — Implementation Plan

**Status:** all twelve steps in §8 are built. Everything in §7 remains out
of scope. Two decisions changed during the build and are recorded in place:
the v1 schema needs no migration runner (§3), and a shift ending before it
starts runs past midnight (§4).

## 1. Overview

A desktop application for managing employee work shifts. A manager uses the
app to maintain a list of employees, create shifts, assign employees to
shifts, and view coverage on a calendar/roster. No login/authentication —
it runs as a single local desktop app with full access to whoever runs it.

- **Language:** Python 3.11+
- **GUI:** Tkinter (+ `ttk` for themed widgets)
- **Storage:** SQLite (via the built-in `sqlite3` module)
- **Platform target:** cross-platform desktop (Windows/macOS/Linux)

## 2. Core Features (v1 scope)

1. **Employee management**
   - Add / edit / deactivate employees (name, role/position, contact info,
     hourly rate optional, color tag for calendar display).
   - List view with search/filter.
2. **Shift management**
   - Define shift templates (e.g. "Morning", "Evening", "Night") with
     default start/end times.
   - Create individual shift instances on specific dates, optionally from a
     template or fully custom (date, start time, end time, notes).
   - Edit / delete shifts.
3. **Assignment**
   - Assign one or more employees to a shift.
   - Prevent double-booking: warn/block if an employee is already assigned
     to an overlapping shift on the same day.
   - Unassign / reassign employees.
4. **Calendar / roster view**
   - Weekly view (primary) showing shifts per day with assigned employees.
   - Navigate between weeks (prev/next/today).
   - Optional monthly overview (stretch goal, see §7).
   - Click a shift to view/edit details and assignments.
5. **Reporting**
   - Per-employee scheduled hours summary for a selected date range
     (week/month).
   - Simple text/CSV export of the roster for a date range.
6. **Data persistence**
   - All data stored in a local SQLite file (default: `data/shifts.db`,
     configurable).
   - App creates/initializes the DB and schema on first run if missing.

### Out of scope for v1 (explicitly deferred)
- Authentication / multi-user roles.
- Clock-in/clock-out time tracking (actual vs. scheduled hours).
- Payroll calculation.
- Shift-swap requests / employee self-service.
- Notifications/reminders (email, desktop notifications).
- Multi-location / multi-department support.
- Recurring shift patterns (e.g. "every Monday") — may be a stretch goal.

## 3. Architecture

Layered structure to keep GUI, business logic, and data access separate so
each can be tested and modified independently.

```
work_shift_manager/
├── planning/
│   └── PLAN.md
├── src/
│   └── shiftmanager/
│       ├── __init__.py
│       ├── main.py              # app entry point, wires everything together
│       ├── db/
│       │   ├── __init__.py
│       │   ├── connection.py    # sqlite3 connection helper, PRAGMA setup
│       │   └── schema.sql       # CREATE TABLE IF NOT EXISTS statements
│       ├── models/
│       │   ├── __init__.py
│       │   ├── employee.py      # Employee dataclass
│       │   ├── shift.py         # Shift / ShiftTemplate dataclasses
│       │   └── assignment.py    # Assignment dataclass
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── employee_repo.py     # CRUD for employees
│       │   ├── shift_repo.py        # CRUD for shifts/templates
│       │   └── assignment_repo.py   # CRUD + overlap-check queries
│       ├── services/
│       │   ├── __init__.py
│       │   ├── scheduling_service.py  # assignment rules, conflict detection
│       │   └── report_service.py      # hours summaries, CSV export
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── app.py               # root Tk window, navigation/menu
│       │   ├── employee_view.py     # employee list/add/edit frames
│       │   ├── shift_view.py        # shift create/edit dialogs
│       │   ├── calendar_view.py     # weekly roster grid + navigation
│       │   ├── assignment_dialog.py # assign employees to a shift
│       │   ├── report_view.py       # hours summary / export screen
│       │   └── widgets/
│       │       └── __init__.py      # small reusable widgets (date picker, etc.)
│       └── utils/
│           ├── __init__.py
│           └── datetime_utils.py    # week bounds, overlap checks, formatting
├── tests/
│   ├── test_repositories.py
│   ├── test_scheduling_service.py
│   └── test_report_service.py
├── data/
│   └── shifts.db                # created at runtime, git-ignored
├── pyproject.toml                # uv project config; no runtime deps (see §9)
├── .gitignore
└── README.md
```

**Layer responsibilities:**
- `db/`: connection management and raw schema only. The schema is applied
  with `CREATE TABLE IF NOT EXISTS` on every connect, so v1 needs no
  migration runner; add one only when a released schema has to change.
- `models/`: plain dataclasses representing domain entities, no DB logic.
- `repositories/`: SQL queries, translate rows ↔ model objects. Only layer
  that touches `sqlite3` directly.
- `services/`: business rules that span repositories (e.g. conflict
  detection needs both shift and assignment data).
- `gui/`: Tkinter frames/dialogs. Calls services/repositories, never raw SQL.

## 4. Data Model (SQLite schema, draft)

```sql
CREATE TABLE employees (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    position      TEXT,
    phone         TEXT,
    email         TEXT,
    hourly_rate   REAL,
    color_tag     TEXT,           -- hex color for calendar display
    is_active     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE shift_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,     -- e.g. "Morning"
    start_time  TEXT NOT NULL,     -- "HH:MM"
    end_time    TEXT NOT NULL      -- "HH:MM"
);

CREATE TABLE shifts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id   INTEGER REFERENCES shift_templates(id),
    shift_date    TEXT NOT NULL,   -- "YYYY-MM-DD"
    start_time    TEXT NOT NULL,   -- "HH:MM"
    end_time      TEXT NOT NULL,   -- "HH:MM"
    notes         TEXT
);

CREATE TABLE assignments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    shift_id     INTEGER NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,
    employee_id  INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(shift_id, employee_id)
);

CREATE INDEX idx_shifts_date ON shifts(shift_date);
CREATE INDEX idx_assignments_employee ON assignments(employee_id);
```

Overlap detection (for double-booking prevention) is done in
`scheduling_service.py` by querying an employee's assignments for a given
date and comparing start/end times in Python (SQLite has no native time
overlap operator).

A shift whose `end_time` is earlier than its `start_time` runs past
midnight and ends the following day — 22:00 to 06:00 is an eight hour
overnight shift. Conflict checks therefore scan the day either side of the
shift being assigned, while hours always count towards the day the shift
starts on. Shifts that merely touch (09:00-17:00 then 17:00-22:00) do not
conflict.

## 5. GUI Design (Tkinter)

- **Main window (`app.py`)**: menu bar (File, Employees, Reports) or a
  left-side navigation panel with buttons: *Roster*, *Employees*,
  *Reports*. A content `Frame` on the right swaps between views
  (simple frame-switching pattern, no extra framework needed).
- **Roster/Calendar view**: a `ttk.Frame` with a header (week range +
  prev/next/today buttons) and a grid of day columns (Mon–Sun) built from
  `ttk.Treeview` or stacked `Frame`/`Label` widgets per shift card.
  Clicking a shift opens the assignment dialog (`Toplevel`).
- **Employee view**: `ttk.Treeview` list + Add/Edit/Deactivate buttons,
  opening a form dialog (`Toplevel`) for create/edit.
- **Shift dialog**: form for date, template selection (autofills
  start/end) or custom times, notes.
- **Assignment dialog**: multi-select list of active employees (e.g.
  `Listbox` with `MULTIPLE` mode or checkbuttons) with conflict warnings
  shown inline before confirming.
- **Reports view**: date-range pickers + employee filter, results in a
  `ttk.Treeview`, "Export CSV" button.
- Styling: `ttk` themed widgets throughout for a consistent look; a small
  `styles.py` (in `gui/`) may centralize fonts/colors if needed.

## 6. Testing Strategy

- Unit tests (via `pytest` or stdlib `unittest`) for:
  - Repository CRUD operations (using an in-memory SQLite DB,
    `sqlite3.connect(":memory:")`).
  - `scheduling_service` conflict-detection logic (overlap edge cases).
  - `report_service` hour-summation logic.
- GUI is manually tested (Tkinter unit testing has poor ROI); a short
  manual test checklist will be included in the README once built:
  add employee → create shift → assign → verify conflict warning →
  view roster → export report.

## 7. Stretch Goals (post-v1, not part of initial build)

- Recurring shift patterns / bulk shift creation.
- Monthly calendar view.
- Simple login with admin/employee roles.
- Clock-in/clock-out actual-hours tracking.
- Printable/PDF roster export.
- Dark mode / theme switcher.

## 8. Build Order

1. Project scaffolding (`src/` layout, `pyproject.toml` via `uv init`,
   `.gitignore`).
2. `db/` connection + schema creation on first run.
3. `models/` dataclasses.
4. `repositories/` with unit tests against an in-memory DB.
5. `services/` (scheduling conflict detection, reporting) with unit tests.
6. `gui/app.py` shell with navigation between empty placeholder views.
7. Employee view (list, add, edit, deactivate).
8. Shift + template management (create/edit).
9. Assignment dialog with conflict warnings, wired into calendar view.
10. Calendar/roster weekly view (the main screen).
11. Reports view + CSV export.
12. Manual end-to-end pass, polish (styling, error handling on bad input),
    update README with run instructions.

## 9. Dependencies

- Standard library only for v1: `tkinter`, `sqlite3`, `dataclasses`,
  `datetime`, `csv`. No third-party runtime packages required.
- `uv` manages the project (`pyproject.toml`). Setup is `uv sync`, launch is
  `uv run python -m shiftmanager.main`.
- `pytest` as the only dev dependency, for the test suite.
