"""Modal form for creating and editing a shift."""

import tkinter as tk
from tkinter import messagebox, ttk

from shiftmanager.models import Shift
from shiftmanager.repositories import shift_repo
from shiftmanager.utils import parse_date, parse_time

NO_TEMPLATE = "(none)"


class ShiftDialog(tk.Toplevel):
    """Collects shift details, returning None when cancelled.

    Picking a template fills in its start and end times; the times are then
    free to edit, and are always stored on the shift itself.
    """

    def __init__(self, parent, conn, title: str, shift: Shift | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result: Shift | None = None
        self.conn = conn
        self._shift = shift
        self._templates = shift_repo.list_templates(conn)

        self._date = tk.StringVar()
        self._start = tk.StringVar()
        self._end = tk.StringVar()
        self._notes = tk.StringVar()
        self._template = tk.StringVar(value=NO_TEMPLATE)

        self._build()
        self._prefill(shift)

        self.transient(parent)
        self.grab_set()

    def show(self) -> Shift | None:
        """Wait for the dialog to close and return what was entered."""
        self.wait_window()
        return self.result

    def _build(self) -> None:
        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Date").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self._date, width=28).grid(
            row=0, column=1, sticky="ew", padx=(12, 0), pady=4
        )
        ttk.Label(form, text="YYYY-MM-DD", foreground="grey").grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )

        ttk.Label(form, text="Template").grid(row=1, column=0, sticky="w", pady=4)
        picker = ttk.Combobox(
            form,
            textvariable=self._template,
            state="readonly",
            values=[NO_TEMPLATE] + [t.name for t in self._templates],
        )
        picker.grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=4)
        picker.bind("<<ComboboxSelected>>", lambda _: self._apply_template())

        for row, (label, variable, hint) in enumerate(
            (("Start", self._start, "HH:MM"), ("End", self._end, "HH:MM")), start=2
        ):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(form, textvariable=variable, width=28).grid(
                row=row, column=1, sticky="ew", padx=(12, 0), pady=4
            )
            ttk.Label(form, text=hint, foreground="grey").grid(
                row=row, column=2, sticky="w", padx=(8, 0)
            )

        ttk.Label(form, text="Notes").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self._notes, width=28).grid(
            row=4, column=1, sticky="ew", padx=(12, 0), pady=4
        )

        buttons = ttk.Frame(self, padding=(16, 0, 16, 16))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", command=self._save).pack(
            side="right", padx=(0, 8)
        )
        self.bind("<Return>", lambda _: self._save())
        self.bind("<Escape>", lambda _: self.destroy())

    def _prefill(self, shift: Shift | None) -> None:
        if shift is None:
            return
        self._date.set(shift.shift_date)
        self._start.set(shift.start_time)
        self._end.set(shift.end_time)
        self._notes.set(shift.notes or "")
        named = self._template_by_id(shift.template_id)
        self._template.set(named.name if named else NO_TEMPLATE)

    def _apply_template(self) -> None:
        template = self._template_by_name(self._template.get())
        if template:
            self._start.set(template.start_time)
            self._end.set(template.end_time)

    def _template_by_name(self, name: str):
        return next((t for t in self._templates if t.name == name), None)

    def _template_by_id(self, template_id):
        return next((t for t in self._templates if t.id == template_id), None)

    def _save(self) -> None:
        date_text = self._date.get().strip()
        start_text = self._start.get().strip()
        end_text = self._end.get().strip()

        try:
            parse_date(date_text)
        except ValueError:
            self._complain("Invalid date", f"'{date_text}' is not YYYY-MM-DD.")
            return

        for label, value in (("start", start_text), ("end", end_text)):
            try:
                parse_time(value)
            except ValueError:
                self._complain("Invalid time", f"The {label} time '{value}' is not HH:MM.")
                return

        if start_text == end_text:
            self._complain(
                "Empty shift", "The start and end times are the same."
            )
            return

        template = self._template_by_name(self._template.get())
        self.result = Shift(
            id=self._shift.id if self._shift else None,
            template_id=template.id if template else None,
            shift_date=date_text,
            start_time=start_text,
            end_time=end_text,
            notes=self._notes.get().strip() or None,
        )
        self.destroy()

    def _complain(self, title: str, message: str) -> None:
        messagebox.showerror(title, message, parent=self)
