# Work Shift Manager

Tkinter desktop app for managing employee work shifts: employees, shifts,
assignments, a weekly roster, and hours reports. Single local app, no
authentication. Full design in `planning/PLAN.md` — read it before
implementing; keep it updated when decisions change.

## Stack

- Python 3.11+, standard library only (`tkinter`, `sqlite3`, `dataclasses`,
  `datetime`, `csv`). No third-party runtime dependencies.
- `uv` for packaging and execution. `pytest` as the only dev dependency.
- SQLite file at `data/shifts.db`, created with its schema on first run.

## Commands

```bash
uv sync                       # install deps
uv run python -m shiftmanager.main   # launch the GUI
uv run pytest                 # run the test suite
uv run pytest tests/test_scheduling_service.py   # single test file
uv add --dev <pkg>            # add a dev dependency
```

Never call `python`/`pip` directly — always `uv run` / `uv add`.

## Layering

Strict one-way dependencies: `gui` → `services` → `repositories` → `db`,
with `models` and `utils` usable from anywhere.

| Layer | Holds | Must not |
| --- | --- | --- |
| `db/` | connection helper, `schema.sql` | know about domain rules |
| `models/` | plain dataclasses | touch SQL or Tk |
| `repositories/` | all SQL; rows ↔ model objects | hold business rules |
| `services/` | rules spanning repositories (conflicts, reports) | import `tkinter` |
| `gui/` | Tk frames and dialogs | write raw SQL |

SQL statements appear only under `db/` and `repositories/`. Elsewhere
`sqlite3` may be imported solely for the `Connection` type annotation.
`tkinter` is imported only under `gui/` and `main.py`.

## Conventions

- Dates are `"YYYY-MM-DD"` strings, times `"HH:MM"` strings, in both the DB
  and the model dataclasses. Convert to `datetime` only inside
  `utils/datetime_utils.py` for comparisons and formatting.
- Shift overlap / double-booking checks live in
  `services/scheduling_service.py`, computed in Python — not in SQL.
- An `end_time` before `start_time` means the shift runs past midnight into
  the next day. Hours count towards the day the shift starts on.
- Repositories take an open `sqlite3.Connection`; they never open their own.
- Employees are deactivated (`is_active = 0`), never deleted.
- `ttk` widgets throughout, not raw `tk` ones, for consistent theming.
- Short modules and functions, clear names, docstrings over inline comments.
- No emojis anywhere in code, output, or logs.

## Testing

`pytest` against an in-memory DB (`sqlite3.connect(":memory:")`) for
repositories, scheduling conflict edge cases, and report hour sums. The GUI
is verified manually — see the checklist in `README.md`.

## Scope

v1 is the feature list in PLAN.md §2. Everything in §7 (recurring shifts,
monthly view, login/roles, clock-in tracking, PDF export, dark mode) is out
of scope — do not add it unasked. Follow the build order in PLAN.md §8,
validating each step before starting the next.
