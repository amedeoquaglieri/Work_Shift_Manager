"""Roster screen.

For now it lists every shift in a table. The Monday to Sunday grid and week
navigation replace that table in a later build step; the toolbar stays.
"""

from tkinter import messagebox, ttk

from shiftmanager.gui.shift_dialog import ShiftDialog
from shiftmanager.gui.template_manager import TemplateManager
from shiftmanager.repositories import shift_repo

COLUMNS = (
    ("shift_date", "Date", 110),
    ("start_time", "Start", 70),
    ("end_time", "End", 70),
    ("template", "Template", 130),
    ("notes", "Notes", 260),
)


class CalendarView(ttk.Frame):
    """Lists shifts and opens the dialogs that create and change them."""

    def __init__(self, parent, conn):
        super().__init__(parent, padding=16)
        self.conn = conn
        self._shifts = {}

        self._build()
        self.refresh()

    def refresh(self) -> None:
        """Reload the shift list from the database."""
        shifts = shift_repo.list_all(self.conn)
        self._shifts = {shift.id: shift for shift in shifts}
        names = {t.id: t.name for t in shift_repo.list_templates(self.conn)}

        self._tree.delete(*self._tree.get_children())
        for shift in shifts:
            self._tree.insert(
                "",
                "end",
                iid=str(shift.id),
                values=(
                    shift.shift_date,
                    shift.start_time,
                    shift.end_time,
                    names.get(shift.template_id, ""),
                    shift.notes or "",
                ),
            )

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        ttk.Label(self, text="Roster", font=("", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="New shift", command=self._add).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self._edit).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(toolbar, text="Delete", command=self._delete).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(
            toolbar, text="Manage templates", command=self._manage_templates
        ).pack(side="right")

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
        shift = ShiftDialog(self, self.conn, "New Shift").show()
        if shift:
            shift_repo.add(self.conn, shift)
            self.refresh()

    def _edit(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        edited = ShiftDialog(self, self.conn, "Edit Shift", shift=selected).show()
        if edited:
            shift_repo.update(self.conn, edited)
            self.refresh()

    def _delete(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        if messagebox.askyesno(
            "Delete shift",
            f"Delete the shift on {selected.shift_date} at {selected.start_time}? "
            "Anyone assigned to it loses that assignment.",
            parent=self,
        ):
            shift_repo.delete(self.conn, selected.id)
            self.refresh()

    def _manage_templates(self) -> None:
        TemplateManager(self, self.conn).wait_window()
        self.refresh()

    def _selected(self):
        """The highlighted shift, warning when nothing is picked."""
        selection = self._tree.selection()
        if not selection:
            messagebox.showinfo(
                "No selection", "Pick a shift from the list first.", parent=self
            )
            return None
        return self._shifts[int(selection[0])]
