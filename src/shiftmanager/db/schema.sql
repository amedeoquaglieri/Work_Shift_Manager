CREATE TABLE IF NOT EXISTS employees (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    position      TEXT,
    phone         TEXT,
    email         TEXT,
    hourly_rate   REAL,
    color_tag     TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS shift_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    start_time  TEXT NOT NULL,
    end_time    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shifts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id   INTEGER REFERENCES shift_templates(id),
    shift_date    TEXT NOT NULL,
    start_time    TEXT NOT NULL,
    end_time      TEXT NOT NULL,
    notes         TEXT
);

CREATE TABLE IF NOT EXISTS assignments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    shift_id     INTEGER NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,
    employee_id  INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE(shift_id, employee_id)
);

CREATE INDEX IF NOT EXISTS idx_shifts_date ON shifts(shift_date);
CREATE INDEX IF NOT EXISTS idx_assignments_employee ON assignments(employee_id);
