"""Employee list with add, edit and deactivate actions."""

import tkinter as tk
from tkinter import messagebox, ttk

from shiftmanager.gui.employee_dialog import EmployeeDialog
from shiftmanager.repositories import employee_repo

COLUMNS = (
    ("name", "Name", 180),
    ("position", "Position", 140),
    ("phone", "Phone", 120),
    ("email", "Email", 200),
    ("hourly_rate", "Rate", 70),
    ("status", "Status", 90),
)


class EmployeeView(ttk.Frame):
    """Lists employees and opens the form dialog to change them."""

    def __init__(self, parent, conn):
        super().__init__(parent, padding=16)
        self.conn = conn
        self._employees = {}
        self._search = tk.StringVar()
        self._show_inactive = tk.BooleanVar(value=False)

        self._build()
        self.refresh()

    def refresh(self) -> None:
        """Reload the list from the database, applying the current filters."""
        employees = employee_repo.list_all(
            self.conn, include_inactive=self._show_inactive.get()
        )
        self._employees = {employee.id: employee for employee in employees}

        self._tree.delete(*self._tree.get_children())
        term = self._search.get().strip().lower()
        for employee in employees:
            if term and term not in self._haystack(employee):
                continue
            self._tree.insert("", "end", iid=str(employee.id), values=self._row(employee))

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        ttk.Label(self, text="Employees", font=("", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(toolbar, text="Search").pack(side="left")
        search = ttk.Entry(toolbar, textvariable=self._search, width=24)
        search.pack(side="left", padx=(8, 16))
        search.bind("<KeyRelease>", lambda _: self.refresh())
        ttk.Checkbutton(
            toolbar,
            text="Show inactive",
            variable=self._show_inactive,
            command=self.refresh,
        ).pack(side="left")

        ttk.Button(toolbar, text="Deactivate", command=self._deactivate).pack(
            side="right"
        )
        ttk.Button(toolbar, text="Edit", command=self._edit).pack(
            side="right", padx=(0, 8)
        )
        ttk.Button(toolbar, text="Add", command=self._add).pack(
            side="right", padx=(0, 8)
        )

        self._tree = ttk.Treeview(
            self, columns=[key for key, _, _ in COLUMNS], show="headings"
        )
        for key, heading, width in COLUMNS:
            self._tree.heading(key, text=heading)
            self._tree.column(key, width=width, anchor="w")
        self._tree.grid(row=2, column=0, sticky="nsew")
        self._tree.bind("<Double-1>", lambda _: self._edit())

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scrollbar.set)

    def _add(self) -> None:
        employee = EmployeeDialog(self, "Add Employee").show()
        if employee:
            employee_repo.add(self.conn, employee)
            self.refresh()

    def _edit(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        edited = EmployeeDialog(self, "Edit Employee", employee=selected).show()
        if edited:
            employee_repo.update(self.conn, edited)
            self.refresh()

    def _deactivate(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        if not selected.is_active:
            messagebox.showinfo(
                "Already inactive", f"{selected.name} is already inactive.", parent=self
            )
            return
        if messagebox.askyesno(
            "Deactivate employee",
            f"Deactivate {selected.name}? Their past shifts are kept.",
            parent=self,
        ):
            employee_repo.deactivate(self.conn, selected.id)
            self.refresh()

    def _selected(self):
        """The highlighted employee, warning when nothing is picked."""
        selection = self._tree.selection()
        if not selection:
            messagebox.showinfo(
                "No selection", "Pick an employee from the list first.", parent=self
            )
            return None
        return self._employees[int(selection[0])]

    @staticmethod
    def _haystack(employee) -> str:
        return f"{employee.name} {employee.position or ''}".lower()

    @staticmethod
    def _row(employee) -> tuple:
        rate = "" if employee.hourly_rate is None else f"{employee.hourly_rate:.2f}"
        return (
            employee.name,
            employee.position or "",
            employee.phone or "",
            employee.email or "",
            rate,
            "Active" if employee.is_active else "Inactive",
        )
