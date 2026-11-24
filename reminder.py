"""reminder.py - background reminder system.

How it works (simple version):
  1. A background THREAD wakes up every few seconds and asks the database:
     "Which appointments start within the next 10 minutes?"
  2. Every new appointment found is put into a QUEUE.
  3. The main window (GUI thread) uses Tkinter's after() to look into the
     queue once per second and shows the pop-up.

Why a queue? Tkinter widgets and message boxes must only be used from the
main thread. The background thread therefore never touches the GUI; it only
hands over the data through the queue.
"""

import queue
import threading
from datetime import datetime, timedelta
from tkinter import messagebox

import database


class ReminderService:
    """Checks for upcoming appointments and shows reminder pop-ups."""

    def __init__(self, root, minutes_before=10, check_interval=20):
        self.root = root                      # the main Tk window
        self.minutes_before = minutes_before  # remind this many minutes early
        self.check_interval = check_interval  # seconds between two checks

        self._queue = queue.Queue()           # thread -> GUI hand-over box
        self._stop_event = threading.Event()  # set when the app is closing
        self._thread = None
        self._after_id = None                 # id of the pending after() call
        self._reminded_ids = set()            # appointments already reminded

    # ------------------------------------------------------------
    # Start / stop
    # ------------------------------------------------------------
    def start(self):
        """Start the background thread and the GUI queue checker."""
        if self._thread is not None and self._thread.is_alive():
            return  # already running
        self._stop_event.clear()
        # daemon=True: the thread cannot keep the program alive after closing
        self._thread = threading.Thread(target=self._worker,
                                        name="ReminderThread", daemon=True)
        self._thread.start()
        self._check_queue()

    def stop(self):
        """Stop the thread and the queue checker (called when closing)."""
        self._stop_event.set()  # wakes the thread immediately
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._thread is not None:
            self._thread.join(timeout=2)

    # ------------------------------------------------------------
    # Background thread (never touches the GUI)
    # ------------------------------------------------------------
    def _worker(self):
        """Runs in the background until the application closes."""
        while not self._stop_event.is_set():
            self._find_due_appointments()
            # wait() sleeps, but wakes up at once if stop() is called
            self._stop_event.wait(self.check_interval)

    def _find_due_appointments(self):
        """Put appointments starting within the reminder window into the queue."""
        now = datetime.now()
        limit = now + timedelta(minutes=self.minutes_before)
        try:
            rows = database.get_appointments_between(now, limit)
        except database.DatabaseError as error:
            print(f"Reminder check failed: {error}")  # try again next time
            return
        for row in rows:
            appointment_id = row[database.COL_ID]
            if appointment_id not in self._reminded_ids:   # avoid repeats
                self._reminded_ids.add(appointment_id)
                self._queue.put(row)

    # ------------------------------------------------------------
    # GUI side (runs in the main thread through after())
    # ------------------------------------------------------------
    def _check_queue(self):
        """Show a pop-up for every waiting reminder, then schedule itself again."""
        if self._stop_event.is_set():
            return
        try:
            while True:
                row = self._queue.get_nowait()
                self._show_popup(row)
        except queue.Empty:
            pass
        if not self._stop_event.is_set():
            self._after_id = self.root.after(1000, self._check_queue)

    def _show_popup(self, row):
        """Display the reminder message box."""
        appointment_dt = datetime.strptime(
            f"{row[database.COL_DATE]} {row[database.COL_TIME]}", database.DATETIME_FORMAT)
        minutes_left = max(0, int((appointment_dt - datetime.now()).total_seconds() // 60))

        self.root.deiconify()   # restore the window if it was minimised
        self.root.lift()        # bring it to the front
        self.root.bell()        # system beep
        messagebox.showinfo(
            "Appointment Reminder",
            f"An appointment starts in about {minutes_left} minute(s)!\n\n"
            f"Customer : {row[database.COL_NAME]}\n"
            f"Date     : {row[database.COL_DATE]}\n"
            f"Time     : {row[database.COL_TIME]}\n"
            f"Purpose  : {row[database.COL_PURPOSE]}",
            parent=self.root)
