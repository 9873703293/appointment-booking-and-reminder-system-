"""database.py - everything that talks to the SQLite database.

No other file writes SQL. The other files only call the functions below.
All queries are parameterised (they use ? placeholders), which keeps the
data safe from SQL injection.

Dates are stored as text 'YYYY-MM-DD' and times as 'HH:MM' (24-hour).
Because of this fixed format, text comparison also sorts them correctly.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime

# The database file is created in the same folder as this script,
# no matter from where the program is started.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appointments.db")

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

STATUS_BOOKED = "Booked"
STATUS_COMPLETED = "Completed"

# Column order used by every SELECT query, and the matching positions.
COLUMNS = ("id, customer_name, phone, email, appointment_date, "
           "appointment_time, purpose, status")
COL_ID, COL_NAME, COL_PHONE, COL_EMAIL, COL_DATE, COL_TIME, COL_PURPOSE, COL_STATUS = range(8)


class DatabaseError(Exception):
    """Raised when any database operation fails."""


class DuplicateSlotError(DatabaseError):
    """Raised when the date and time slot is already booked."""


def get_connection():
    """Open a new connection to the database file."""
    return sqlite3.connect(DB_PATH)


def _run(query, params=(), fetch=None):
    """Run one SQL query safely and return the result.

    fetch = "all"  -> list of rows
    fetch = "one"  -> a single row (or None)
    fetch = None   -> number of rows changed
    A new connection is opened and closed for every call, so the
    reminder thread and the GUI thread never share a connection.
    """
    try:
        with closing(get_connection()) as conn:
            cursor = conn.execute(query, params)
            if fetch == "all":
                result = cursor.fetchall()
            elif fetch == "one":
                result = cursor.fetchone()
            else:
                result = cursor.rowcount
            conn.commit()
            return result
    except sqlite3.IntegrityError as error:
        if "UNIQUE" in str(error).upper():
            raise DuplicateSlotError("This date and time slot is already booked.") from error
        raise DatabaseError(f"Database error: {error}") from error
    except sqlite3.Error as error:
        raise DatabaseError(f"Database error: {error}") from error


def init_db():
    """Create the appointments table if it does not exist yet."""
    _run("""
        CREATE TABLE IF NOT EXISTS appointments (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name    TEXT NOT NULL,
            phone            TEXT NOT NULL,
            email            TEXT,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            purpose          TEXT NOT NULL,
            status           TEXT NOT NULL DEFAULT 'Booked',
            UNIQUE (appointment_date, appointment_time)
        )
    """)


# ---------------------------------------------------------------
# Booking
# ---------------------------------------------------------------
def is_slot_taken(date_text, time_text):
    """Return True if an appointment already exists at this date and time."""
    row = _run(
        "SELECT 1 FROM appointments WHERE appointment_date = ? AND appointment_time = ?",
        (date_text, time_text), fetch="one")
    return row is not None


def add_appointment(name, phone, email, date_text, time_text, purpose):
    """Insert a new appointment with status 'Booked'."""
    _run(
        "INSERT INTO appointments "
        "(customer_name, phone, email, appointment_date, appointment_time, purpose, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, phone, email, date_text, time_text, purpose, STATUS_BOOKED))


# ---------------------------------------------------------------
# Viewing and searching
# ---------------------------------------------------------------
def get_all_appointments():
    """Return all appointments sorted by date and then time."""
    return _run(
        f"SELECT {COLUMNS} FROM appointments "
        "ORDER BY appointment_date, appointment_time", fetch="all")


def search_appointments(keyword):
    """Return appointments whose customer name or phone contains the keyword."""
    pattern = f"%{keyword}%"
    return _run(
        f"SELECT {COLUMNS} FROM appointments "
        "WHERE customer_name LIKE ? OR phone LIKE ? "
        "ORDER BY appointment_date, appointment_time",
        (pattern, pattern), fetch="all")


# ---------------------------------------------------------------
# Cancelling and status management
# ---------------------------------------------------------------
def delete_appointment(appointment_id):
    """Delete (cancel) an appointment. Returns the number of rows deleted."""
    return _run("DELETE FROM appointments WHERE id = ?", (appointment_id,))


def update_status(appointment_id, new_status):
    """Change the status of an appointment (Booked / Completed)."""
    return _run("UPDATE appointments SET status = ? WHERE id = ?",
                (new_status, appointment_id))


# ---------------------------------------------------------------
# Dashboard queries
# ---------------------------------------------------------------
def count_total():
    """Total number of appointments in the database."""
    return _run("SELECT COUNT(*) FROM appointments", fetch="one")[0]


def count_today():
    """Number of appointments dated today."""
    today = datetime.now().strftime(DATE_FORMAT)
    return _run("SELECT COUNT(*) FROM appointments WHERE appointment_date = ?",
                (today,), fetch="one")[0]


def count_upcoming():
    """Number of 'Booked' appointments that are still in the future."""
    now_text = datetime.now().strftime(DATETIME_FORMAT)
    return _run(
        "SELECT COUNT(*) FROM appointments WHERE status = ? "
        "AND (appointment_date || ' ' || appointment_time) >= ?",
        (STATUS_BOOKED, now_text), fetch="one")[0]


def get_today_appointments():
    """All appointments dated today, ordered by time."""
    today = datetime.now().strftime(DATE_FORMAT)
    return _run(
        f"SELECT {COLUMNS} FROM appointments WHERE appointment_date = ? "
        "ORDER BY appointment_time", (today,), fetch="all")


def get_upcoming_appointments(limit=15):
    """The next 'Booked' appointments that are still in the future."""
    now_text = datetime.now().strftime(DATETIME_FORMAT)
    return _run(
        f"SELECT {COLUMNS} FROM appointments WHERE status = ? "
        "AND (appointment_date || ' ' || appointment_time) >= ? "
        "ORDER BY appointment_date, appointment_time LIMIT ?",
        (STATUS_BOOKED, now_text, limit), fetch="all")


# ---------------------------------------------------------------
# Reminder query
# ---------------------------------------------------------------
def get_appointments_between(start_dt, end_dt):
    """'Booked' appointments that start between two datetime values."""
    return _run(
        f"SELECT {COLUMNS} FROM appointments WHERE status = ? "
        "AND (appointment_date || ' ' || appointment_time) >= ? "
        "AND (appointment_date || ' ' || appointment_time) <= ? "
        "ORDER BY appointment_date, appointment_time",
        (STATUS_BOOKED, start_dt.strftime(DATETIME_FORMAT),
         end_dt.strftime(DATETIME_FORMAT)), fetch="all")
