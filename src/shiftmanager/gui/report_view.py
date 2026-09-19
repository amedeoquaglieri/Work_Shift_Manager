"""Scheduled hours report over a date range, with CSV export."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from shiftmanager.repositories import employee_repo
from shiftmanager.services import report_service
from shiftmanager.utils import month_bounds, parse_date, today, week_bounds

ALL_EMPLOYEES = "All employees"

COLUMNS = (
    ("name", "Employee", 200),
    ("position", "Position", 150),
    ("shifts", "Shifts", 80),
    ("hours", "Hours", 80),
)


class ReportView(ttk.Frame):
    """Sums scheduled hours per employee and writes them out as CSV."""

    def __init__(self, parent, conn):
        super().__init__(parent, padding=16)
        self.conn = conn

        start, end = week_bounds(today())
        self._start = tk.StringVar(value=start)
        self._end = tk.StringVar(value=end)
        self._employee = tk.StringVar(value=ALL_EMPLOYEES)
        self._total = tk.StringVar()

        self._build()
        self.refresh()

    def refresh(self) -> None:
        """Reload the employee filter and re-run the report."""
        names = [e.name for e in employee_repo.list_all(self.conn, include_inactive=True)]
        self._picker.configure(values=[ALL_EMPLOYEES] + names)
        if self._employee.get() not in [ALL_EMPLOYEES] + names:
            self._employee.set(ALL_EMPLOYEES)
        self._run()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        ttk.Label(self, text="Reports", font=("", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        dates = ttk.Frame(self)
        dates.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(dates, text="From").pack(side="left")
        ttk.Entry(dates, textvariable=self._start, width=12).pack(
            side="left", padx=(8, 16)
        )
        ttk.Label(dates, text="To").pack(side="left")
        ttk.Entry(dates, textvariable=self._end, width=12).pack(
            side="left", padx=(8, 16)
        )
        ttk.Button(dates, text="This week", command=self._this_week).pack(side="left")
        ttk.Button(dates, text="This month", command=self._this_month).pack(
            side="left", padx=8
        )

        filters = ttk.Frame(self)
        filters.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(filters, text="Employee").pack(side="left")
        self._picker = ttk.Combobox(
            filters, textvariable=self._employee, state="readonly", width=28
        )
        self._picker.pack(side="left", padx=(8, 16))
        self._picker.bind("<<ComboboxSelected>>", lambda _: self._run())
        ttk.Button(filters, text="Run", command=self._run).pack(side="left")
        ttk.Button(filters, text="Export CSV", command=self._export).pack(side="right")

        self._tree = ttk.Treeview(
            self, columns=[key for key, _, _ in COLUMNS], show="headings"
        )
        for key, heading, width in COLUMNS:
            self._tree.heading(key, text=heading)
            self._tree.column(key, width=width, anchor="w")
        self._tree.grid(row=3, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scrollbar.set)

        ttk.Label(self, textvariable=self._total).grid(
            row=4, column=0, sticky="w", pady=(8, 0)
        )

    def _rows(self):
        """The report rows for the chosen range, or None when the dates are bad."""
        start, end = self._start.get().strip(), self._end.get().strip()
        for label, value in (("From", start), ("To", end)):
            try:
                parse_date(value)
            except ValueError:
                messagebox.showerror(
                    "Invalid date",
                    f"The {label} date '{value}' is not YYYY-MM-DD.",
                    parent=self,
                )
                return None

        if start > end:
            messagebox.showerror(
                "Invalid range", "The From date is after the To date.", parent=self
            )
            return None

        rows = report_service.hours_by_employee(self.conn, start, end)
        chosen = self._employee.get()
        if chosen != ALL_EMPLOYEES:
            rows = [row for row in rows if row.employee.name == chosen]
        return rows

    def _run(self) -> None:
        rows = self._rows()
        if rows is None:
            return

        self._tree.delete(*self._tree.get_children())
        for row in rows:
            self._tree.insert(
                "",
                "end",
                values=(
                    row.employee.name,
                    row.employee.position or "",
                    row.shift_count,
                    f"{row.hours:g}",
                ),
            )
        total = round(sum(row.hours for row in rows), 2)
        self._total.set(f"{len(rows)} employees, {total:g} hours scheduled")

    def _export(self) -> None:
        rows = self._rows()
        if rows is None:
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export hours report",
            defaultextension=".csv",
            initialfile=f"hours-{self._start.get()}-to-{self._end.get()}.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        report_service.export_csv(rows, path)
        messagebox.showinfo("Exported", f"Wrote {len(rows)} rows to {path}", parent=self)

    def _this_week(self) -> None:
        start, end = week_bounds(today())
        self._start.set(start)
        self._end.set(end)
        self._run()

    def _this_month(self) -> None:
        start, end = month_bounds(today())
        self._start.set(start)
        self._end.set(end)
        self._run()
