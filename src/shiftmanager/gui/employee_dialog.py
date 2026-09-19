"""Modal form for creating and editing an employee."""

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from shiftmanager.models import Employee

FIELDS = (
    ("name", "Name"),
    ("position", "Position"),
    ("phone", "Phone"),
    ("email", "Email"),
    ("hourly_rate", "Hourly rate"),
)


class EmployeeDialog(tk.Toplevel):
    """Collects employee details, returning None when cancelled."""

    def __init__(self, parent, title: str, employee: Employee | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result: Employee | None = None
        self._employee = employee

        self._entries = {}
        self._color = tk.StringVar(value=employee.color_tag if employee else "")
        self._active = tk.BooleanVar(value=employee.is_active if employee else True)
        self._build(editing=employee is not None)
        self._prefill(employee)

        self.transient(parent)
        self.grab_set()
        self._entries["name"].focus_set()

    def show(self) -> Employee | None:
        """Wait for the dialog to close and return what was entered."""
        self.wait_window()
        return self.result

    def _build(self, editing: bool) -> None:
        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        for row, (key, label) in enumerate(FIELDS):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(form, width=32)
            entry.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=4)
            self._entries[key] = entry

        color_row = len(FIELDS)
        ttk.Label(form, text="Colour").grid(row=color_row, column=0, sticky="w", pady=4)
        colour = ttk.Frame(form)
        colour.grid(row=color_row, column=1, sticky="ew", padx=(12, 0), pady=4)
        ttk.Entry(colour, textvariable=self._color, width=12).pack(side="left")
        ttk.Button(colour, text="Pick...", command=self._pick_colour).pack(
            side="left", padx=(8, 0)
        )

        if editing:
            ttk.Checkbutton(form, text="Active", variable=self._active).grid(
                row=color_row + 1, column=1, sticky="w", padx=(12, 0), pady=4
            )

        buttons = ttk.Frame(self, padding=(16, 0, 16, 16))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Save", command=self._save).pack(
            side="right", padx=(0, 8)
        )
        self.bind("<Return>", lambda _: self._save())
        self.bind("<Escape>", lambda _: self.destroy())

    def _prefill(self, employee: Employee | None) -> None:
        if employee is None:
            return
        for key, _ in FIELDS:
            value = getattr(employee, key)
            if value is not None:
                self._entries[key].insert(0, str(value))

    def _pick_colour(self) -> None:
        chosen = colorchooser.askcolor(parent=self, initialcolor=self._color.get() or None)
        if chosen[1]:
            self._color.set(chosen[1])

    def _save(self) -> None:
        values = {key: self._entries[key].get().strip() for key, _ in FIELDS}
        if not values["name"]:
            messagebox.showerror("Missing name", "An employee needs a name.", parent=self)
            return

        rate = values["hourly_rate"]
        if rate:
            try:
                rate = float(rate)
            except ValueError:
                messagebox.showerror(
                    "Invalid rate", f"'{rate}' is not a number.", parent=self
                )
                return
        else:
            rate = None

        colour = self._color.get().strip()
        if colour and not self._is_drawable(colour):
            messagebox.showerror(
                "Invalid colour",
                f"'{colour}' is not a colour. Use the picker or a hex value "
                "such as #3366cc.",
                parent=self,
            )
            return

        self.result = Employee(
            id=self._employee.id if self._employee else None,
            name=values["name"],
            position=values["position"] or None,
            phone=values["phone"] or None,
            email=values["email"] or None,
            hourly_rate=rate,
            color_tag=colour or None,
            is_active=self._active.get(),
        )
        self.destroy()

    def _is_drawable(self, colour: str) -> bool:
        """Whether Tk can turn the text into a colour."""
        try:
            self.winfo_rgb(colour)
        except tk.TclError:
            return False
        return True
