"""Modal form for creating and editing a shift template."""

import tkinter as tk
from tkinter import messagebox, ttk

from shiftmanager.models import ShiftTemplate
from shiftmanager.utils import parse_time


class TemplateDialog(tk.Toplevel):
    """Collects a template's name and times, returning None when cancelled."""

    def __init__(self, parent, title: str, template: ShiftTemplate | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result: ShiftTemplate | None = None
        self._template = template

        self._name_var = tk.StringVar(value=template.name if template else "")
        self._start = tk.StringVar(value=template.start_time if template else "")
        self._end = tk.StringVar(value=template.end_time if template else "")

        self._build()
        self.transient(parent)
        self.grab_set()

    def show(self) -> ShiftTemplate | None:
        """Wait for the dialog to close and return what was entered."""
        self.wait_window()
        return self.result

    def _build(self) -> None:
        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        rows = (
            ("Name", self._name_var, ""),
            ("Start", self._start, "HH:MM"),
            ("End", self._end, "HH:MM"),
        )
        for row, (label, variable, hint) in enumerate(rows):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(form, textvariable=variable, width=24).grid(
                row=row, column=1, sticky="ew", padx=(12, 0), pady=4
            )
            if hint:
                ttk.Label(form, text=hint, foreground="grey").grid(
                    row=row, column=2, sticky="w", padx=(8, 0)
                )

        buttons = ttk.Frame(self, padding=(16, 0, 16, 16))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", command=self._save).pack(
            side="right", padx=(0, 8)
        )
        self.bind("<Return>", lambda _: self._save())
        self.bind("<Escape>", lambda _: self.destroy())

    def _save(self) -> None:
        name = self._name_var.get().strip()
        start = self._start.get().strip()
        end = self._end.get().strip()

        if not name:
            messagebox.showerror("Missing name", "A template needs a name.", parent=self)
            return

        for label, value in (("start", start), ("end", end)):
            try:
                parse_time(value)
            except ValueError:
                messagebox.showerror(
                    "Invalid time",
                    f"The {label} time '{value}' is not HH:MM.",
                    parent=self,
                )
                return

        if start == end:
            messagebox.showerror(
                "Empty template", "The start and end times are the same.", parent=self
            )
            return

        self.result = ShiftTemplate(
            id=self._template.id if self._template else None,
            name=name,
            start_time=start,
            end_time=end,
        )
        self.destroy()
