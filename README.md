# Appointment Booking and Reminder System

A desktop mini-project built with **Python 3, Tkinter and SQLite**.

## Features
- Dashboard: total, today's and upcoming appointments
- Book an appointment (name, phone, optional email, date, time, purpose)
- Input validation, no past dates/times, no duplicate time slots
- View all appointments (sorted by date and time), search by name or phone
- Cancel an appointment (with confirmation) and mark appointments as Completed
- Background reminder: pop-up 10 minutes before an appointment
  (only while the application is running)

## Files
| File | Responsibility |
|---|---|
| `main.py` | Starts the app; main window, sidebar, page switching, safe closing |
| `database.py` | All SQLite code (create table, insert, select, search, delete, update) |
| `booking.py` | Input validation, Book Appointment page, View/Search/Cancel page |
| `dashboard.py` | Home page with statistics and short tables |
| `reminder.py` | Background thread + queue that shows reminder pop-ups |
| `theme.py` | Shared colours, fonts, button and table styles |
| `appointments.db` | Created automatically on the first run |

## How to run (Windows, VS Code)
1. Install Python 3.8+ from python.org (tick **Add Python to PATH**).
2. In VS Code choose **File > Open Folder** and open `Appointment_Booking_System`.
3. Install the VS Code **Python** extension.
4. Open `main.py` and click the **Run** button, or type in the terminal:
   `python main.py`

No external libraries are needed.

## Date and time format
- Date: `YYYY-MM-DD` (example `2026-12-05`)
- Time: `HH:MM`, 24-hour (example `14:30`)

## Quick reminder test
Book an appointment about 12-15 minutes from now and keep the app open.
The pop-up appears about 10 minutes before the appointment time
(the check runs every 20 seconds). Booking an appointment less than
10 minutes ahead shows the reminder almost immediately.

## Troubleshooting
- *"No module named tkinter"*: reinstall Python and keep **tcl/tk and IDLE** ticked.
- *"no such column" error*: delete an old `appointments.db` file and run again.
