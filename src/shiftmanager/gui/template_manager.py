"""Window listing shift templates, with add, edit and delete."""

import tkinter as tk
from tkinter import messagebox, ttk

from shiftmanager.gui.template_dialog import TemplateDialog
from shiftmanager.repositories import shift_repo

COLUMNS = (("name", "Name", 160), ("start_time", "Start", 80), ("end_time", "End", 80))


class TemplateManager(tk.Toplevel):
    """Manages the reusable shift times offered by the shift dialog."""

    def __init__(self, parent, conn):
        super().__init__(parent)
        self.title("Shift Templates")
        self.geometry("420x320")
        self.conn = conn
        self._templates = {}

        self._build()
        self.refresh()

        self.transient(parent)
        self.grab_set()

    def refresh(self) -> None:
        """Reload the template list from the database."""
        templates = shift_repo.list_templates(self.conn)
        self._templates = {template.id: template for template in templates}

        self._tree.delete(*self._tree.get_children())
        for template in templates:
            self._tree.insert(
                "",
                "end",
                iid=str(template.id),
                values=(template.name, template.start_time, template.end_time),
            )

    def _build(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            container, columns=[key for key, _, _ in COLUMNS], show="headings"
        )
        for key, heading, width in COLUMNS:
            self._tree.heading(key, text=heading)
            self._tree.column(key, width=width, anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._tree.bind("<Double-1>", lambda _: self._edit())

        buttons = ttk.Frame(container)
        buttons.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(buttons, text="Add", command=self._add).pack(side="left")
        ttk.Button(buttons, text="Edit", command=self._edit).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(buttons, text="Delete", command=self._delete).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(buttons, text="Close", command=self.destroy).pack(side="right")

    def _add(self) -> None:
        template = TemplateDialog(self, "Add Template").show()
        if template:
            shift_repo.add_template(self.conn, template)
            self.refresh()

    def _edit(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        edited = TemplateDialog(self, "Edit Template", template=selected).show()
        if edited:
            shift_repo.update_template(self.conn, edited)
            self.refresh()

    def _delete(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        if messagebox.askyesno(
            "Delete template",
            f"Delete '{selected.name}'? Shifts already created from it keep "
            "their times.",
            parent=self,
        ):
            shift_repo.delete_template(self.conn, selected.id)
            self.refresh()

    def _selected(self):
        """The highlighted template, warning when nothing is picked."""
        selection = self._tree.selection()
        if not selection:
            messagebox.showinfo(
                "No selection", "Pick a template from the list first.", parent=self
            )
            return None
        return self._templates[int(selection[0])]
