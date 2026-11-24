"""main.py - starting point of the Appointment Booking and Reminder System.

Run this file to start the application:   python main.py

It creates the main window, the sidebar, and the three pages
(Dashboard, Book Appointment, View Appointments), and starts the
background reminder service.
"""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import database
from theme import COLORS, FONT_HEADING, FONT_NORMAL, FONT_BUTTON, make_button, apply_styles
from dashboard import DashboardPage
from booking import BookingPage, AppointmentsPage
from reminder import ReminderService


class AppointmentApp(tk.Tk):
    """The main application window."""

    # Names shown on the sidebar buttons (also used as page keys)
    PAGE_DASHBOARD = "Dashboard"
    PAGE_BOOK = "Book Appointment"
    PAGE_VIEW = "View Appointments"

    def __init__(self):
        super().__init__()
        self.title("Appointment Booking and Reminder System")
        self.geometry("1150x700")
        self.minsize(980, 600)          # window is resizable, but not too small
        self.configure(bg=COLORS["bg"])

        apply_styles()                  # table (Treeview) colours
        self.pages = {}
        self.nav_buttons = {}
        self.current_page = None

        self._build_sidebar()
        self._build_pages()
        self.show_page(self.PAGE_DASHBOARD)

        self._update_clock()
        self._auto_refresh()

        # Start the background reminders
        self.reminders = ReminderService(self, minutes_before=10, check_interval=20)
        self.reminders.start()

        # Ask before closing and stop the thread safely
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------
    def _build_sidebar(self):
        """Left navigation panel."""
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)   # keep the fixed width

        tk.Label(sidebar, text="Appointment\nBooking &\nReminder System",
                 font=FONT_HEADING, bg=COLORS["sidebar"], fg="white",
                 justify="left").pack(anchor="w", padx=25, pady=(30, 30))

        for name in (self.PAGE_DASHBOARD, self.PAGE_BOOK, self.PAGE_VIEW):
            button = tk.Button(
                sidebar, text=name, anchor="w", padx=25, pady=13,
                font=FONT_BUTTON, relief="flat", bd=0, cursor="hand2",
                bg=COLORS["sidebar"], fg="white",
                activebackground=COLORS["sidebar_hover"], activeforeground="white",
                command=lambda page=name: self.show_page(page))
            button.pack(fill="x")
            # Hover effect (the active page keeps its own colour)
            button.bind("<Enter>", lambda e, b=button, n=name: self._on_hover(b, n, True))
            button.bind("<Leave>", lambda e, b=button, n=name: self._on_hover(b, n, False))
            self.nav_buttons[name] = button

        # Bottom of the sidebar: exit button and clock
        make_button(sidebar, "Exit", self.on_close, COLORS["danger"]).pack(
            side="bottom", fill="x", padx=20, pady=20)
        self.clock_label = tk.Label(sidebar, text="", font=FONT_NORMAL,
                                    bg=COLORS["sidebar"], fg="#cbd5e1")
        self.clock_label.pack(side="bottom", pady=5)

    def _build_pages(self):
        """Create all pages and stack them on top of each other."""
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(side="right", fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        page_classes = {
            self.PAGE_DASHBOARD: DashboardPage,
            self.PAGE_BOOK: BookingPage,
            self.PAGE_VIEW: AppointmentsPage,
        }
        for name, page_class in page_classes.items():
            page = page_class(container)
            page.grid(row=0, column=0, sticky="nsew")   # all in the same cell
            self.pages[name] = page

    # ------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------
    def show_page(self, name):
        """Bring one page to the front and reload its data."""
        self.current_page = name
        page = self.pages[name]
        page.refresh()
        page.tkraise()
        for page_name, button in self.nav_buttons.items():
            button.config(bg=COLORS["sidebar_active"] if page_name == name
                          else COLORS["sidebar"])

    def _on_hover(self, button, name, inside):
        """Change the sidebar button colour while the mouse is over it."""
        if name == self.current_page:
            return
        button.config(bg=COLORS["sidebar_hover"] if inside else COLORS["sidebar"])

    # ------------------------------------------------------------
    # Repeating jobs (use after(), so the GUI never freezes)
    # ------------------------------------------------------------
    def _update_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%d %b %Y\n%I:%M:%S %p"))
        self.after(1000, self._update_clock)

    def _auto_refresh(self):
        """Refresh the dashboard every 30 seconds while it is visible."""
        if self.current_page == self.PAGE_DASHBOARD:
            self.pages[self.PAGE_DASHBOARD].refresh()
        self.after(30000, self._auto_refresh)

    # ------------------------------------------------------------
    # Closing
    # ------------------------------------------------------------
    def on_close(self):
        """Ask for confirmation, stop the reminder thread, close the window."""
        if messagebox.askokcancel(
                "Exit", "Do you want to close the application?\n"
                        "Reminders work only while the application is open.", parent=self):
            self.reminders.stop()
            self.destroy()


def main():
    # Create the database and table automatically (first run).
    try:
        database.init_db()
    except database.DatabaseError as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Database Error", f"Could not start the application.\n\n{error}")
        root.destroy()
        return

    app = AppointmentApp()
    app.mainloop()


if __name__ == "__main__":
    main()
