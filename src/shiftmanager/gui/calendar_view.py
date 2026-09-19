"""Weekly roster: seven day columns of shift cards, with week navigation."""

import tkinter as tk
from tkinter import messagebox, ttk

from shiftmanager.gui.assignment_dialog import AssignmentDialog
from shiftmanager.gui.shift_dialog import ShiftDialog
from shiftmanager.gui.template_manager import TemplateManager
from shiftmanager.repositories import assignment_repo, shift_repo
from shiftmanager.utils import (
    add_days,
    format_weekday,
    today,
    week_dates,
    week_start,
)

TODAY_COLOUR = "#0b6bcb"
MUTED_COLOUR = "grey"


class CalendarView(ttk.Frame):
    """Shows one week at a time and opens the shift and staffing dialogs."""

    def __init__(self, parent, conn):
        super().__init__(parent, padding=16)
        self.conn = conn
        self._week_start = week_start(today())
        self._range = tk.StringVar()

        self._build()
        self.refresh()

    def refresh(self) -> None:
        """Rebuild the grid for the week currently being shown."""
        dates = week_dates(self._week_start)
        self._range.set(f"{format_weekday(dates[0])} - {format_weekday(dates[6])}")

        for column in self._grid.winfo_children():
            column.destroy()

        shifts = self._shifts_by_date(dates[0], dates[6])
        for index, date in enumerate(dates):
            self._grid.columnconfigure(index, weight=1, uniform="day")
            self._build_column(index, date, shifts.get(date, []))

    def _shifts_by_date(self, start_date: str, end_date: str) -> dict:
        """The week's shifts, grouped by the day they start on."""
        grouped = {}
        for shift in shift_repo.list_between(self.conn, start_date, end_date):
            grouped.setdefault(shift.shift_date, []).append(shift)
        return grouped

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        ttk.Label(self, text="Roster", font=("", 16, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(toolbar, text="< Previous", command=self._previous_week).pack(
            side="left"
        )
        ttk.Button(toolbar, text="Today", command=self._this_week).pack(
            side="left", padx=8
        )
        ttk.Button(toolbar, text="Next >", command=self._next_week).pack(side="left")
        ttk.Label(toolbar, textvariable=self._range, font=("", 11, "bold")).pack(
            side="left", padx=16
        )
        ttk.Button(
            toolbar, text="Manage templates", command=self._manage_templates
        ).pack(side="right")

        body = ttk.Frame(self)
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        canvas = tk.Canvas(body, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._grid = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=self._grid, anchor="nw")
        self._grid.bind(
            "<Configure>",
            lambda _: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window, width=event.width),
        )

    def _build_column(self, index: int, date: str, shifts: list) -> None:
        column = ttk.Frame(self._grid, padding=(2, 0))
        column.grid(row=0, column=index, sticky="nsew")

        header = ttk.Frame(column)
        header.pack(fill="x")
        is_today = date == today()
        ttk.Label(
            header,
            text=format_weekday(date),
            font=("", 9, "bold"),
            foreground=TODAY_COLOUR if is_today else "",
        ).pack(side="left")
        ttk.Button(
            header, text="+", width=2, command=lambda d=date: self._add(d)
        ).pack(side="right")

        if not shifts:
            ttk.Label(column, text="-", foreground=MUTED_COLOUR).pack(
                anchor="w", pady=4
            )
        for shift in shifts:
            self._build_card(column, shift)

    def _build_card(self, parent: ttk.Frame, shift) -> None:
        card = ttk.Labelframe(
            parent, text=f"{shift.start_time} - {shift.end_time}", padding=6
        )
        card.pack(fill="x", pady=3)

        staff = assignment_repo.employees_for_shift(self.conn, shift.id)
        if not staff:
            ttk.Label(card, text="unstaffed", foreground=MUTED_COLOUR).pack(anchor="w")
        for employee in staff:
            ttk.Label(
                card,
                text=employee.name,
                foreground=_usable_colour(card, employee.color_tag),
            ).pack(anchor="w")

        if shift.notes:
            ttk.Label(card, text=shift.notes, foreground=MUTED_COLOUR).pack(anchor="w")

        _bind_deep(card, "<Button-1>", lambda _, s=shift: self._assign(s))
        _bind_deep(card, "<Button-3>", lambda event, s=shift: self._menu(event, s))

    def _menu(self, event, shift) -> None:
        """Right-click menu offering the actions for one shift."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Assign staff", command=lambda: self._assign(shift))
        menu.add_command(label="Edit shift", command=lambda: self._edit(shift))
        menu.add_command(label="Delete shift", command=lambda: self._delete(shift))
        menu.tk_popup(event.x_root, event.y_root)

    def _add(self, date: str) -> None:
        shift = ShiftDialog(self, self.conn, "New Shift", default_date=date).show()
        if shift:
            shift_repo.add(self.conn, shift)
            self.refresh()

    def _edit(self, shift) -> None:
        edited = ShiftDialog(self, self.conn, "Edit Shift", shift=shift).show()
        if edited:
            shift_repo.update(self.conn, edited)
            self.refresh()

    def _delete(self, shift) -> None:
        if messagebox.askyesno(
            "Delete shift",
            f"Delete the shift on {shift.shift_date} at {shift.start_time}? "
            "Anyone assigned to it loses that assignment.",
            parent=self,
        ):
            shift_repo.delete(self.conn, shift.id)
            self.refresh()

    def _assign(self, shift) -> None:
        if AssignmentDialog(self, self.conn, shift).show():
            self.refresh()

    def _manage_templates(self) -> None:
        TemplateManager(self, self.conn).wait_window()
        self.refresh()

    def _previous_week(self) -> None:
        self._week_start = add_days(self._week_start, -7)
        self.refresh()

    def _next_week(self) -> None:
        self._week_start = add_days(self._week_start, 7)
        self.refresh()

    def _this_week(self) -> None:
        self._week_start = week_start(today())
        self.refresh()


def _usable_colour(widget, colour: str | None) -> str:
    """The colour if Tk can draw it, otherwise the default foreground.

    Colour tags are free text and may predate validation, and an unusable
    one would otherwise stop the whole window from opening.
    """
    if not colour:
        return ""
    try:
        widget.winfo_rgb(colour)
    except tk.TclError:
        return ""
    return colour


def _bind_deep(widget, sequence: str, handler) -> None:
    """Bind an event on a widget and everything drawn inside it.

    Clicks land on whichever label sits under the pointer, so the whole card
    has to carry the binding for the card to feel clickable.
    """
    widget.bind(sequence, handler)
    for child in widget.winfo_children():
        _bind_deep(child, sequence, handler)
