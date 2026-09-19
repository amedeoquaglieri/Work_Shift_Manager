"""Modal dialog for choosing who works a shift."""

import tkinter as tk
from tkinter import messagebox, ttk

from shiftmanager.models import Shift
from shiftmanager.repositories import assignment_repo, employee_repo
from shiftmanager.services import scheduling_service


class AssignmentDialog(tk.Toplevel):
    """Ticks employees on and off a shift, warning about clashes.

    Conflicts are shown beside each name while choosing, and confirmed again
    on save, so a double-booking is always deliberate.
    """

    def __init__(self, parent, conn, shift: Shift):
        super().__init__(parent)
        self.title("Assign Staff")
        self.geometry("520x420")
        self.conn = conn
        self.changed = False
        self._shift = shift
        self._checks = {}

        self._assigned = {
            employee.id
            for employee in assignment_repo.employees_for_shift(conn, shift.id)
        }
        self._build()

        self.transient(parent)
        self.grab_set()

    def show(self) -> bool:
        """Wait for the dialog to close, reporting whether anything changed."""
        self.wait_window()
        return self.changed

    def _candidates(self):
        """Active employees, plus anyone already on this shift."""
        employees = employee_repo.list_all(self.conn, include_inactive=True)
        return [e for e in employees if e.is_active or e.id in self._assigned]

    def _build(self) -> None:
        header = ttk.Frame(self, padding=(16, 16, 16, 8))
        header.pack(fill="x")
        ttk.Label(
            header,
            text=f"{self._shift.shift_date}  {self._shift.start_time} - "
            f"{self._shift.end_time}",
            font=("", 12, "bold"),
        ).pack(anchor="w")

        body = ttk.Frame(self, padding=(16, 0, 16, 8))
        body.pack(fill="both", expand=True)

        canvas = tk.Canvas(body, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        rows = ttk.Frame(canvas)
        rows.bind(
            "<Configure>",
            lambda _: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=rows, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        candidates = self._candidates()
        if not candidates:
            ttk.Label(rows, text="No employees yet. Add some first.").pack(anchor="w")

        for employee in candidates:
            self._add_row(rows, employee)

        buttons = ttk.Frame(self, padding=(16, 0, 16, 16))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", command=self._save).pack(
            side="right", padx=(0, 8)
        )
        self.bind("<Escape>", lambda _: self.destroy())

    def _add_row(self, parent: ttk.Frame, employee) -> None:
        checked = tk.BooleanVar(value=employee.id in self._assigned)
        self._checks[employee.id] = checked

        row = ttk.Frame(parent)
        row.pack(fill="x", anchor="w", pady=1)

        label = employee.name if employee.is_active else f"{employee.name} (inactive)"
        ttk.Checkbutton(row, text=label, variable=checked).pack(side="left")

        clashes = scheduling_service.find_conflicts(self.conn, employee.id, self._shift)
        if clashes:
            ttk.Label(
                row, text=f"clashes with {_describe(clashes)}", foreground="#b00020"
            ).pack(side="left", padx=(8, 0))

    def _save(self) -> None:
        selected = {eid for eid, checked in self._checks.items() if checked.get()}
        to_add = selected - self._assigned
        to_remove = self._assigned - selected

        clashing = {}
        for employee_id in to_add:
            conflicts = scheduling_service.find_conflicts(
                self.conn, employee_id, self._shift
            )
            if conflicts:
                clashing[employee_id] = conflicts

        if clashing and not self._confirm(clashing):
            return

        for employee_id in to_add:
            scheduling_service.assign(
                self.conn, self._shift.id, employee_id, force=True
            )
        for employee_id in to_remove:
            assignment_repo.remove(self.conn, self._shift.id, employee_id)

        self.changed = bool(to_add or to_remove)
        self.destroy()

    def _confirm(self, clashing: dict) -> bool:
        """Ask before double-booking, naming each clash."""
        names = {e.id: e.name for e in self._candidates()}
        lines = [
            f"{names[employee_id]} already works {_describe(conflicts)}"
            for employee_id, conflicts in clashing.items()
        ]
        return messagebox.askyesno(
            "Double booking",
            "\n".join(lines) + "\n\nAssign anyway?",
            parent=self,
        )


def _describe(shifts: list[Shift]) -> str:
    """A short, readable summary of the clashing shifts."""
    return ", ".join(
        f"{shift.shift_date} {shift.start_time}-{shift.end_time}" for shift in shifts
    )
