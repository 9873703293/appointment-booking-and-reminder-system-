"""dashboard.py - the home page.

Shows three summary cards (total / today / upcoming) and two small tables:
today's appointments and the next upcoming appointments.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

import database
from theme import COLORS, FONT_TITLE, FONT_HEADING, FONT_NORMAL, FONT_SMALL


class DashboardPage(tk.Frame):
    """Home page with statistics and short appointment lists."""

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self._build_ui()

    # ------------------------------------------------------------
    # Building the screen
    # ------------------------------------------------------------
    def _build_ui(self):
        tk.Label(self, text="Dashboard", font=FONT_TITLE, bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", padx=30, pady=(25, 0))
        self.date_label = tk.Label(self, text="", font=FONT_NORMAL,
                                   bg=COLORS["bg"], fg=COLORS["muted"])
        self.date_label.pack(anchor="w", padx=30, pady=(0, 15))

        # ----- three statistic cards -----
        cards = tk.Frame(self, bg=COLORS["bg"])
        cards.pack(fill="x", padx=25)
        self.total_value = self._make_stat_card(cards, 0, "Total Appointments", COLORS["primary"])
        self.today_value = self._make_stat_card(cards, 1, "Today's Appointments", COLORS["success"])
        self.upcoming_value = self._make_stat_card(cards, 2, "Upcoming Appointments", COLORS["warning"])

        # ----- two tables side by side -----
        tables = tk.Frame(self, bg=COLORS["bg"])
        tables.pack(fill="both", expand=True, padx=25, pady=20)
        tables.columnconfigure(0, weight=1, uniform="tables")
        tables.columnconfigure(1, weight=1, uniform="tables")
        tables.rowconfigure(0, weight=1)

        self.today_tree = self._make_table(
            tables, 0, "Today's Appointments",
            (("time", "Time", 70), ("name", "Customer", 150),
             ("purpose", "Purpose", 170), ("status", "Status", 80)))
        self.upcoming_tree = self._make_table(
            tables, 1, "Upcoming Appointments",
            (("date", "Date", 95), ("time", "Time", 65),
             ("name", "Customer", 140), ("purpose", "Purpose", 160)))

    def _make_stat_card(self, parent, column, title, color):
        """Create one coloured number card and return its value label."""
        parent.columnconfigure(column, weight=1, uniform="stats")
        card = tk.Frame(parent, bg=color, padx=20, pady=16)
        card.grid(row=0, column=column, sticky="nsew", padx=5)
        value = tk.Label(card, text="0", font=("Segoe UI", 32, "bold"),
                         bg=color, fg="white")
        value.pack(anchor="w")
        tk.Label(card, text=title, font=FONT_NORMAL, bg=color, fg="white").pack(anchor="w")
        return value

    def _make_table(self, parent, column, title, columns):
        """Create a white card containing a heading and a Treeview table."""
        card = tk.Frame(parent, bg=COLORS["card"],
                        highlightbackground=COLORS["border"], highlightthickness=1)
        card.grid(row=0, column=column, sticky="nsew", padx=5)
        tk.Label(card, text=title, font=FONT_HEADING, bg=COLORS["card"],
                 fg=COLORS["text"]).pack(anchor="w", padx=12, pady=(10, 6))

        holder = tk.Frame(card, bg=COLORS["card"])
        holder.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        tree = ttk.Treeview(holder, columns=[c[0] for c in columns],
                            show="headings", height=8, selectmode="none")
        for column_id, heading, width in columns:
            tree.heading(column_id, text=heading)
            tree.column(column_id, width=width, minwidth=40, anchor="w")
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    # ------------------------------------------------------------
    # Loading data
    # ------------------------------------------------------------
    def refresh(self):
        """Reload the numbers and tables from the database."""
        self.date_label.config(text=datetime.now().strftime("Today is %A, %d %B %Y"))
        try:
            self.total_value.config(text=str(database.count_total()))
            self.today_value.config(text=str(database.count_today()))
            self.upcoming_value.config(text=str(database.count_upcoming()))
            today_rows = database.get_today_appointments()
            upcoming_rows = database.get_upcoming_appointments(15)
        except database.DatabaseError as error:
            # Refresh also runs automatically, so do not pop up a box each time.
            print(f"Dashboard could not load data: {error}")
            return

        self._fill(self.today_tree, [
            (r[database.COL_TIME], r[database.COL_NAME],
             r[database.COL_PURPOSE], r[database.COL_STATUS]) for r in today_rows])
        self._fill(self.upcoming_tree, [
            (r[database.COL_DATE], r[database.COL_TIME],
             r[database.COL_NAME], r[database.COL_PURPOSE]) for r in upcoming_rows])

    @staticmethod
    def _fill(tree, rows):
        """Replace all rows of a Treeview with the given rows."""
        for item in tree.get_children():
            tree.delete(item)
        for values in rows:
            tree.insert("", tk.END, values=values)
