"""booking.py - input validation and the two appointment pages.

Contains:
  validate_appointment()  - checks everything the user typed
  BookingPage             - the "Book Appointment" form
  AppointmentsPage        - view, search, cancel and complete appointments
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import database
from theme import (COLORS, FONT_TITLE, FONT_NORMAL, FONT_SMALL, make_button)

# Simple pattern: something@something.something
EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")


# =====================================================================
# VALIDATION
# =====================================================================
def validate_appointment(name, phone, email, date_text, time_text, purpose):
    """Check all form values.

    Returns (error_message, None) if something is wrong, or
    (None, clean_data) if everything is correct.
    """
    name = name.strip()
    phone = phone.strip()
    email = email.strip()
    date_text = date_text.strip()
    time_text = time_text.strip()
    purpose = purpose.strip()

    # --- customer name ---
    if not name:
        return "Customer name is required.", None
    if len(name) < 2 or not all(ch.isalpha() or ch in " .'-" for ch in name):
        return "Customer name should contain only letters and spaces.", None

    # --- phone: exactly 10 digits ---
    if not (phone.isdigit() and len(phone) == 10):
        return "Phone number must contain exactly 10 digits.", None

    # --- email is optional, but must be valid if typed ---
    if email and not EMAIL_PATTERN.match(email):
        return "Email address is not valid (example: name@example.com).", None

    # --- date ---
    try:
        date_value = datetime.strptime(date_text, database.DATE_FORMAT)
    except ValueError:
        return "Enter the date as YYYY-MM-DD (example: 2026-12-05).", None

    # --- time ---
    try:
        time_value = datetime.strptime(time_text, database.TIME_FORMAT)
    except ValueError:
        return "Enter the time as HH:MM in 24-hour format (example: 14:30).", None

    # --- must not be in the past ---
    appointment_dt = datetime.combine(date_value.date(), time_value.time())
    if appointment_dt <= datetime.now():
        return "The appointment date and time cannot be in the past.", None

    # --- purpose ---
    if len(purpose) < 3:
        return "Please enter the purpose of the appointment.", None

    clean = {
        "name": name,
        "phone": phone,
        "email": email,
        # Re-formatting makes '9:30' become '09:30', so duplicates are detected.
        "date": date_value.strftime(database.DATE_FORMAT),
        "time": time_value.strftime(database.TIME_FORMAT),
        "purpose": purpose,
    }
    return None, clean


# =====================================================================
# BOOK APPOINTMENT PAGE
# =====================================================================
class BookingPage(tk.Frame):
    """The form used to book a new appointment."""

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.entries = {}
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Book New Appointment", font=FONT_TITLE,
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", padx=30, pady=(25, 2))
        tk.Label(self, text="Fields marked with * are required.", font=FONT_NORMAL,
                 bg=COLORS["bg"], fg=COLORS["muted"]).pack(anchor="w", padx=30)

        card = tk.Frame(self, bg=COLORS["card"], padx=30, pady=25,
                        highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(anchor="nw", padx=30, pady=20)

        fields = [
            ("Customer Name *", "name"),
            ("Phone Number * (10 digits)", "phone"),
            ("Email Address (optional)", "email"),
            ("Appointment Date * (YYYY-MM-DD)", "date"),
            ("Appointment Time * (HH:MM, 24-hour)", "time"),
            ("Purpose of Appointment *", "purpose"),
        ]
        for row, (label, key) in enumerate(fields):
            tk.Label(card, text=label, font=FONT_NORMAL, bg=COLORS["card"],
                     fg=COLORS["text"], anchor="w").grid(row=row, column=0, sticky="w",
                                                         pady=9, padx=(0, 25))
            entry = tk.Entry(card, font=FONT_NORMAL, width=38, relief="solid", bd=1)
            entry.grid(row=row, column=1, pady=9, ipady=5)
            self.entries[key] = entry

        # Buttons
        button_row = tk.Frame(card, bg=COLORS["card"])
        button_row.grid(row=len(fields), column=0, columnspan=2, pady=(18, 0), sticky="w")
        make_button(button_row, "Submit Appointment", self.submit,
                    COLORS["success"]).pack(side="left", padx=(0, 10))
        make_button(button_row, "Clear Form", self.clear_form,
                    COLORS["warning"]).pack(side="left")

        tk.Label(self, text="Tip: the date is pre-filled with today's date. "
                            "Example time: 14:30",
                 font=FONT_SMALL, bg=COLORS["bg"], fg=COLORS["muted"]).pack(anchor="w", padx=30)

        self.clear_form()

    def clear_form(self):
        """Empty every box and pre-fill today's date."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.entries["date"].insert(0, datetime.now().strftime(database.DATE_FORMAT))
        self.entries["name"].focus_set()

    def refresh(self):
        """Called each time this page is shown (nothing to reload here)."""
        self.entries["name"].focus_set()

    def submit(self):
        """Validate the form, check for a duplicate slot and save."""
        values = {key: entry.get() for key, entry in self.entries.items()}
        error, data = validate_appointment(
            values["name"], values["phone"], values["email"],
            values["date"], values["time"], values["purpose"])
        if error:
            messagebox.showerror("Invalid Input", error, parent=self)
            return

        try:
            if database.is_slot_taken(data["date"], data["time"]):
                messagebox.showwarning(
                    "Slot Not Available",
                    f"An appointment is already booked on {data['date']} at {data['time']}.\n"
                    "Please choose a different time.", parent=self)
                return
            database.add_appointment(data["name"], data["phone"], data["email"],
                                     data["date"], data["time"], data["purpose"])
        except database.DuplicateSlotError:
            messagebox.showwarning("Slot Not Available",
                                   "This date and time slot is already booked.", parent=self)
            return
        except database.DatabaseError as error:
            messagebox.showerror("Database Error", str(error), parent=self)
            return

        messagebox.showinfo(
            "Success",
            f"Appointment booked successfully!\n\nCustomer: {data['name']}\n"
            f"Date: {data['date']}\nTime: {data['time']}", parent=self)
        self.clear_form()


# =====================================================================
# VIEW / SEARCH / CANCEL PAGE
# =====================================================================
class AppointmentsPage(tk.Frame):
    """Table of appointments with search, cancel and mark-completed."""

    # (column id, heading text, width in pixels)
    COLUMNS = (
        ("id", "ID", 50),
        ("name", "Customer Name", 190),
        ("phone", "Phone", 120),
        ("date", "Date", 100),
        ("time", "Time", 70),
        ("purpose", "Purpose", 260),
        ("status", "Status", 90),
    )

    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.search_var = tk.StringVar()
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="Appointments", font=FONT_TITLE, bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", padx=30, pady=(25, 10))

        # ----- search bar -----
        toolbar = tk.Frame(self, bg=COLORS["bg"])
        toolbar.pack(fill="x", padx=30)
        tk.Label(toolbar, text="Search by name or phone:", font=FONT_NORMAL,
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
        search_entry = tk.Entry(toolbar, textvariable=self.search_var, font=FONT_NORMAL,
                                width=28, relief="solid", bd=1)
        search_entry.pack(side="left", padx=10, ipady=4)
        search_entry.bind("<Return>", lambda event: self.search())  # Enter key works too
        make_button(toolbar, "Search", self.search, COLORS["primary"]).pack(side="left", padx=4)
        make_button(toolbar, "Refresh / Show All", self.refresh,
                    COLORS["info"]).pack(side="left", padx=4)

        # ----- table -----
        table_frame = tk.Frame(self, bg=COLORS["card"],
                               highlightbackground=COLORS["border"], highlightthickness=1)
        table_frame.pack(fill="both", expand=True, padx=30, pady=15)

        self.tree = ttk.Treeview(table_frame, columns=[c[0] for c in self.COLUMNS],
                                 show="headings", selectmode="browse")
        for column_id, heading, width in self.COLUMNS:
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=width, minwidth=40,
                             anchor="center" if column_id in ("id", "time", "status") else "w")
        self.tree.tag_configure("completed", foreground="#9ca3af")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ----- action buttons -----
        bottom = tk.Frame(self, bg=COLORS["bg"])
        bottom.pack(fill="x", padx=30, pady=(0, 20))
        make_button(bottom, "Mark as Completed", self.mark_completed,
                    COLORS["success"]).pack(side="left", padx=(0, 10))
        make_button(bottom, "Cancel Appointment", self.cancel_appointment,
                    COLORS["danger"]).pack(side="left")
        self.count_label = tk.Label(bottom, text="", font=FONT_SMALL,
                                    bg=COLORS["bg"], fg=COLORS["muted"])
        self.count_label.pack(side="right")

    # ----- loading data -----
    def refresh(self):
        """Clear the search box and show all appointments."""
        self.search_var.set("")
        self._reload()

    def _reload(self):
        """Load the table. Uses the search text if there is one."""
        keyword = self.search_var.get().strip()
        try:
            rows = (database.search_appointments(keyword) if keyword
                    else database.get_all_appointments())
        except database.DatabaseError as error:
            messagebox.showerror("Database Error", str(error), parent=self)
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            tags = ("completed",) if row[database.COL_STATUS] == database.STATUS_COMPLETED else ()
            self.tree.insert(
                "", tk.END, iid=str(row[database.COL_ID]), tags=tags,
                values=(row[database.COL_ID], row[database.COL_NAME], row[database.COL_PHONE],
                        row[database.COL_DATE], row[database.COL_TIME],
                        row[database.COL_PURPOSE], row[database.COL_STATUS]))
        self.count_label.config(text=f"Showing {len(rows)} appointment(s)")

    def search(self):
        """Search by customer name or phone number."""
        if not self.search_var.get().strip():
            messagebox.showinfo("Search", "Please type a name or phone number to search.",
                                parent=self)
            return
        self._reload()
        if not self.tree.get_children():
            messagebox.showinfo("Search", "No matching appointments found.", parent=self)

    # ----- actions on the selected row -----
    def _selected_id(self):
        """Return the id of the selected row, or None (with a warning)."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection",
                                   "Please select an appointment from the table first.",
                                   parent=self)
            return None
        return int(selection[0])  # the row's iid is the appointment id

    def cancel_appointment(self):
        """Ask for confirmation, then delete the selected appointment."""
        appointment_id = self._selected_id()
        if appointment_id is None:
            return
        name = self.tree.set(str(appointment_id), "name")
        date_text = self.tree.set(str(appointment_id), "date")
        time_text = self.tree.set(str(appointment_id), "time")

        confirmed = messagebox.askyesno(
            "Confirm Cancellation",
            f"Do you really want to cancel the appointment of {name}\n"
            f"on {date_text} at {time_text}?\n\nThis will delete the record permanently.",
            parent=self)
        if not confirmed:
            return
        try:
            database.delete_appointment(appointment_id)
        except database.DatabaseError as error:
            messagebox.showerror("Database Error", str(error), parent=self)
            return
        messagebox.showinfo("Cancelled", "The appointment was cancelled successfully.",
                            parent=self)
        self._reload()

    def mark_completed(self):
        """Change the status of the selected appointment to 'Completed'."""
        appointment_id = self._selected_id()
        if appointment_id is None:
            return
        if self.tree.set(str(appointment_id), "status") == database.STATUS_COMPLETED:
            messagebox.showinfo("Status", "This appointment is already completed.", parent=self)
            return
        try:
            database.update_status(appointment_id, database.STATUS_COMPLETED)
        except database.DatabaseError as error:
            messagebox.showerror("Database Error", str(error), parent=self)
            return
        self._reload()
