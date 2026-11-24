"""theme.py - shared colours, fonts and small GUI helpers.

Every page imports its colours and fonts from here, so the whole
application has one consistent look and the design can be changed
in a single place.
"""

import tkinter as tk
from tkinter import ttk

# ---------- Colour palette ----------
COLORS = {
    "sidebar": "#1f2a44",        # dark blue sidebar
    "sidebar_hover": "#2c3b5e",  # sidebar button on mouse hover
    "sidebar_active": "#2563eb", # sidebar button of the current page
    "bg": "#f4f6fb",             # light grey page background
    "card": "#ffffff",           # white cards / forms
    "border": "#e5e7eb",
    "text": "#1f2937",
    "muted": "#6b7280",
    "primary": "#2563eb",        # blue
    "success": "#16a34a",        # green
    "danger": "#dc2626",         # red
    "warning": "#f59e0b",        # orange
    "info": "#0891b2",           # teal
}

# ---------- Fonts ----------
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_HEADING = ("Segoe UI", 13, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_BUTTON = ("Segoe UI", 10, "bold")


def make_button(parent, text, command, color, width=None):
    """Create a flat, coloured button.

    tk.Button is used (not ttk.Button) because it allows a background colour.
    """
    button = tk.Button(
        parent, text=text, command=command,
        bg=color, fg="white",
        activebackground=color, activeforeground="white",
        font=FONT_BUTTON, relief="flat", bd=0,
        cursor="hand2", padx=16, pady=8,
    )
    if width:
        button.config(width=width)
    return button


def apply_styles():
    """Give every Treeview table a clean, modern look.

    Must be called after the main window (tk.Tk) has been created.
    """
    style = ttk.Style()
    style.theme_use("clam")  # 'clam' theme allows colour changes on Windows
    style.configure(
        "Treeview", background="white", fieldbackground="white",
        foreground=COLORS["text"], rowheight=28, font=FONT_NORMAL,
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading", background=COLORS["primary"],
        foreground="white", font=("Segoe UI", 10, "bold"), relief="flat",
    )
    style.map("Treeview.Heading", background=[("active", "#1d4ed8")])
    style.map(
        "Treeview",
        background=[("selected", "#bfdbfe")],
        foreground=[("selected", COLORS["text"])],
    )
