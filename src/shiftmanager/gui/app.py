"""Root window: a navigation sidebar beside a swappable content area."""

import tkinter as tk
from tkinter import ttk

from shiftmanager.gui.calendar_view import CalendarView
from shiftmanager.gui.employee_view import EmployeeView

WINDOW_TITLE = "Work Shift Manager"
VIEW_NAMES = ("Roster", "Employees", "Reports")


class App(tk.Tk):
    """The main application window.

    Takes an open database connection and hands it to the views, which is
    all the wiring the views need to reach the services below them.
    """

    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.title(WINDOW_TITLE)
        self.geometry("1000x640")
        self.minsize(820, 520)

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._views = {}
        self._build_sidebar()
        self._build_content()
        self.show("Roster")

    def show(self, name: str) -> None:
        """Bring one view to the front of the content area."""
        self._views[name].tkraise()

    def _build_sidebar(self) -> None:
        sidebar = ttk.Frame(self, padding=12)
        sidebar.grid(row=0, column=0, sticky="ns")

        ttk.Label(sidebar, text=WINDOW_TITLE, font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 16)
        )
        for name in VIEW_NAMES:
            ttk.Button(
                sidebar, text=name, width=16, command=lambda n=name: self.show(n)
            ).pack(fill="x", pady=2)

    def _build_content(self) -> None:
        content = ttk.Frame(self)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        builders = {
            "Roster": lambda parent: CalendarView(parent, self.conn),
            "Employees": lambda parent: EmployeeView(parent, self.conn),
            "Reports": lambda parent: _placeholder(parent, "Reports"),
        }
        for name in VIEW_NAMES:
            view = builders[name](content)
            view.grid(row=0, column=0, sticky="nsew")
            self._views[name] = view


def _placeholder(parent: ttk.Frame, name: str) -> ttk.Frame:
    """A stand-in view, replaced as each real view is built."""
    frame = ttk.Frame(parent, padding=24)
    ttk.Label(frame, text=name, font=("", 16, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Not built yet.").pack(anchor="w", pady=(8, 0))
    return frame
