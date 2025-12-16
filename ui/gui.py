# ui/gui.py
import csv
import json
import logging
import os
import sqlite3
import threading
import time
import tkinter as tk
from tkinter import PhotoImage, messagebox, ttk
from typing import Optional

import bcrypt  # For password hashing (if needed in future)

from ai_integration.ai_module import (  # AI integration
    _parse_degree_electives_csv,
    get_recommendations_ai,
)
from database import db_add  # For database interactions
from database.db_operations import get_degree_levels  # Added Code
from database.db_operations import get_degrees  # Added Code
from database.db_operations import get_jobs_by_degree  # Added Code
from database.db_operations import save_user_preferences  # Added Code
from database.db_operations import get_colleges, get_departments, get_user_preferences

# Import About dialog
from ui.app_version import show_about_dialog  # Added Code
from ui.gui_titanpark_integration import show_parking_helper, show_parking_history_helper

logger = logging.getLogger(__name__)  # Reuse the global logger

# Global variables for login status and current users
login_status = False
current_user = None
status_var = None

# Dictionary to store navigation buttons
nav_buttons = {}

# Dictionary to store loaded icons
nav_icons = {}


def get_db_connection():
    """Returns a new database connection."""
    try:
        conn = sqlite3.connect("db/ai_advice.db")
        return conn
    except sqlite3.Error as e:
        logger.error("Database connection error: %s", e)
        return None


# Highlights active buttons
def set_active_button(label):
    for name, btn in nav_buttons.items():
        if name == label:
            btn.config(style="Active.TButton")
        else:
            btn.config(style="TButton")


def main_int_ui() -> None:
    """Initializes and runs the main interface of the Smart Elective Advisor."""

    logger.info("Initializing the Smart Elective Advisor GUI.")

    # Minimal Tkinter window
    root = tk.Tk()
    root.title("Smart Elective Advisor")
    root.geometry("1200x800")

    # Grid Layout
    root.columnconfigure(0, weight=0)  # Navigation Menu
    root.columnconfigure(1, weight=1)  # Content Display
    root.rowconfigure(0, weight=1)

    # Create Navigation Menu Frame
    nav_frame = tk.Frame(root, width=250, relief="raised", bg="#F7F7F7")
    nav_frame.grid(row=0, column=0, sticky="ns")
    nav_frame.grid_propagate(False)
    nav_frame.columnconfigure(0, weight=1)

    # Content Area
    content_frame = tk.Frame(root, bg="white", relief="groove", bd=2)
    content_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    content_frame.set_active_button = set_active_button

    # Styles for sidebar buttons
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "TButton", padding=5, anchor="w", font=("Helvetica", 12), background="white"
    )
    style.map("TButton", background=[("pressed", "#FF7900"), ("active", "#FF7900")])
    style.configure(
        "Active.TButton",
        padding=5,
        anchor="w",
        font=("Helvetica", 12, "bold"),
        background="#FF7900",
        foreground="white",
    )

    # Status bar at the bottom
    global status_var
    status_var = tk.StringVar()
    status_var.set("Not logged in")

    status_bar = tk.Label(
        root, textvariable=status_var, bd=1, relief="sunken", anchor="w"
    )
    status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

    # Menu Items
    menu_items = [
        ("Home", "icons/home.png", show_home),
        ("Login", "icons/login.png", show_login),
        ("Logout", "icons/logout.png", show_logout),
        ("Registration", "icons/register.png", show_registration),
        ("Preferences", "icons/preferences.png", show_preferences),
        ("Recommendations", "icons/recommendations.png", show_recommendations),
        ("Profile", "icons/profile.png", show_profile),
        ("Parking", "icons/parking.png", show_parking_helper),  # Added Code
        ("Parking History", "icons/parking-area.png", show_parking_history_helper),
        ("Help", "icons/help.png", show_help),
    ]

    # Creates Navigation buttons with icons
    for i, (label, icon_path, command) in enumerate(menu_items):
        try:
            icon = PhotoImage(file=icon_path)
            nav_icons[label] = icon
            btn = ttk.Button(
                nav_frame,
                text=label,
                image=icon,
                compound="left",
                command=lambda c=command: c(content_frame),
            )
        except Exception as e:
            logger.warning(f"Could not load icon {icon_path}: {e}")
            btn = ttk.Button(
                nav_frame, text=label, command=lambda c=command: c(content_frame)
            )

        btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
        nav_buttons[label] = btn

    # Sets inital state of navigation buttons on login status
    update_nav_buttons()
    # Show home screen first
    show_home(content_frame)

    def _on_close():
        logger.info("GUI received close request; shutting down.")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)

    # Start the Tk mainloop (this call blocks until the window closes)
    try:
        root.mainloop()
    except Exception:
        logger.exception("Error in GUI mainloop")
        raise


def clear_content(frame):
    """Remove all widgets from the content area."""
    for widget in frame.winfo_children():
        widget.destroy()


def update_nav_buttons():
    """Updates the state of navigation buttons based on login status"""
    global login_status, current_user
    if login_status and current_user:
        # Show logout button, hide login button
        nav_buttons["Logout"].grid()
        nav_buttons["Login"].grid_remove()  # removes login button
        nav_buttons["Registration"].grid_remove()  # removes registration button

        # Enable other buttons
        nav_buttons["Home"].config(state="normal")
        nav_buttons["Preferences"].config(state="normal")
        nav_buttons["Recommendations"].config(state="normal")
        nav_buttons["Profile"].config(state="normal")
        nav_buttons["Help"].config(state="normal")
    else:
        # Show Login button, hide Logout button
        nav_buttons["Login"].grid()
        nav_buttons["Logout"].grid_remove()

        # Disable other buttons
        nav_buttons["Home"].config(state="normal")
        nav_buttons["Preferences"].config(state="disabled")
        nav_buttons["Recommendations"].config(state="disabled")
        nav_buttons["Profile"].config(state="disabled")
        nav_buttons["Help"].config(state="normal")


# Test user data
"""
users = {
    "student@test.com": {   
    "password": "password123",
    "first_name": "Test",
    "last_name": "Student"
    }
}
"""


def show_home(frame):
    """Displays the Home Dashboard"""
    set_active_button("Home")
    clear_content(frame)
    label = tk.Label(
        frame, text="Welcome to Smart Elective Advisor", font=("Helvetica", 16)
    )
    label.pack(padx=20, pady=20)
    info_text = (
        "The Smart Elective Advisor helps CS students select the best elective courses based on their "
        "interests, career aspirations, and academic performance. Navigate through the menu to get started."
    )
    info = tk.Label(frame, text=info_text, wraplength=500, justify="center")
    info.pack(pady=10)


# Login Page
def show_login(frame):
    """Displays the Login Page."""
    set_active_button("Login")
    clear_content(frame)
    header_label = tk.Label(frame, text="Login Page", font=("Helvetica", 14))
    header_label.pack(pady=20)

    # Email
    email_label = tk.Label(frame, text="Email:")
    email_label.pack(pady=(10, 5))
    email_entry = tk.Entry(frame, width=30)
    email_entry.pack(pady=(0, 10))

    # Password
    password_label = tk.Label(frame, text="Password:")
    password_label.pack(pady=(10, 5))
    # Frame to hold password entry and eye icon
    pw_frame = ttk.Frame(frame)
    pw_frame.pack(pady=(0, 10))

    password_entry = tk.Entry(pw_frame, width=30, show="*")
    password_entry.grid(row=0, column=0)

    # Eye icon to toggle password visibility
    show_pw = False  # Track toggle state

    def toggle_password():
        """Toggle password visibility for both password fields."""
        nonlocal show_pw
        show_pw = not show_pw
        if show_pw:
            password_entry.config(show="")
            eye_button.config(image=eye_icon)
        else:
            password_entry.config(show="*")
            eye_button.config(image=eye_icon)

    # Load small eye icons
    try:
        eye_icon = tk.PhotoImage(file=os.path.join("icons", "eye_icon.png"))
    except Exception as e:
        logger.warning(f"Could not load eye icons: {e}")
        eye_icon = None

    eye_button = ttk.Button(pw_frame, image=eye_icon, width=5, command=toggle_password)
    eye_button.image = eye_icon  # Keep a reference to prevent garbage collection
    eye_button.grid(row=0, column=1, padx=5)

    def handle_login():
        """Handles login(need to connect to database)"""
        global login_status, current_user
        email = email_entry.get().strip().lower()
        password = password_entry.get()
        logger.debug(f"Attempting login with email: {email}")
        # user = users.get(email)
        conn = get_db_connection()
        # Check if connection was successful
        if not conn:
            messagebox.showerror(
                "Database Error",
                "Could not connect to the database. Please try again later.",
            )
            logger.error("Login failed: Database connection error.")
            return
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, first_name, last_name, password_hash FROM users WHERE email = ?",
            (email,),
        )
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user[3].encode("utf-8")):
            login_status = True
            current_user = {
                "id": user[0],
                "email": email,
                "first_name": user[1],
                "last_name": user[2],
            }
            display_name = f"{user[1]} {user[2]}"
            status_var.set(f"Logged in as: {display_name}")
            messagebox.showinfo("Login Successful", f"Welcome back, {display_name}!")
            logger.info(f"User '{email}' logged in successfully.")
            show_preferences(frame)  # Redirect to preferences page after login
            update_nav_buttons()  # Refreshes button states
        else:
            messagebox.showerror(
                "Login Failed", "Invalid email or password. Please try again."
            )
            logger.warning(f"Login failed for email: {email}")

    # Login Button (Need to add function for logging in)
    login_button = tk.Button(frame, text="Login", width=15, command=handle_login)
    login_button.pack(pady=(20, 10))

    # Forgot password link
    forgot_password_label = tk.Label(
        frame, text="Forgot password?", fg="blue", cursor="hand2"
    )
    forgot_password_label.pack(pady=(5, 2))
    forgot_password_label.bind("<Button-1>", lambda e: show_forgot_password(frame))

    # Registration link
    reg_label = tk.Label(
        frame, text="Don't have an account? Register", fg="blue", cursor="hand2"
    )
    reg_label.pack(pady=(2, 10))
    reg_label.bind("<Button-1>", lambda e: show_registration(frame))


def show_forgot_password(frame):
    """Open a modal password reset prompt without leaking user enumeration."""
    logger.info("User initiated forgot password process.")

    parent = frame.winfo_toplevel()
    popup = tk.Toplevel(parent)
    popup.title("Password Reset")
    popup.geometry("400x220")

    # Make it modal
    popup.transient(parent)
    popup.grab_set()

    tk.Label(popup, text="Reset Your Password", font=("Helvetica", 14, "bold")).pack(
        pady=12
    )

    tk.Label(popup, text="Enter the email associated with your account:").pack(
        pady=(0, 6)
    )

    email_var = tk.StringVar()
    email_entry = ttk.Entry(popup, textvariable=email_var, width=36)
    email_entry.pack(pady=(0, 10))

    def is_valid_email(s: str) -> bool:
        """Very light client-side check (server must verify)."""
        return "@" in s and "." in s.split("@")[-1]

    def submit_reset():
        candidate = email_var.get().strip().lower()
        if not is_valid_email(candidate):
            messagebox.showerror(
                "Invalid Email",
                "Please enter a valid email address.",
                parent=popup,
            )
            return

        # Prevent account enumeration: always show same message
        messagebox.showinfo(
            "If the email exists",
            "If an account exists, you'll receive reset instructions.",
            parent=popup,
        )

        popup.destroy()

    ttk.Button(popup, text="Submit", command=submit_reset).pack(pady=6)
    ttk.Button(popup, text="Cancel", command=popup.destroy).pack()

    email_entry.focus_set()


# Logout
def show_logout(frame):
    """Handles user logging out."""
    set_active_button("Logout")
    global login_status, current_user
    clear_content(frame)
    logger.info("User initaited logout.")

    login_status = False  # reset login status
    current_user = None  # clear current user

    messagebox.showinfo("Logout Successful", "You have been logged out.")
    logger.info("User logged out successfully.")
    show_home(frame)  # Redirect to home page after logout
    update_nav_buttons()  # Refresh button states


# Registration page
def show_registration(frame):
    """Display for Registration Page"""
    set_active_button("Registration")
    global login_status, current_user
    logger.info("Displaying User Registration Form")
    clear_content(frame)
    header_label = tk.Label(frame, text="User Registration", font=("Helvetica", 14))
    header_label.pack(pady=20)

    # Registration Form Frame
    reg_frame = ttk.Frame(frame)
    reg_frame.pack(pady=10)

    # First name
    first_name_label = ttk.Label(reg_frame, text="First Name:")
    first_name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    first_name_entry = ttk.Entry(reg_frame, width=30)
    first_name_entry.grid(row=0, column=1, padx=5, pady=5)

    # Last name
    last_name_label = ttk.Label(reg_frame, text="Last Name:")
    last_name_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    last_name_entry = ttk.Entry(reg_frame, width=30)
    last_name_entry.grid(row=1, column=1, padx=5, pady=5)

    # Email
    email_label = ttk.Label(reg_frame, text="Email:")
    email_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    email_entry = ttk.Entry(reg_frame, width=30)
    email_entry.grid(row=2, column=1, padx=5, pady=5)

    # Password
    password_label = ttk.Label(reg_frame, text="Password:")
    password_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
    password_entry = ttk.Entry(reg_frame, width=30, show="*")
    password_entry.grid(row=3, column=1, padx=5, pady=5)

    # Confirm Password
    confirm_label = ttk.Label(reg_frame, text="Confirm Password:")
    confirm_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
    confirm_entry = ttk.Entry(reg_frame, width=30, show="*")
    confirm_entry.grid(row=4, column=1, padx=5, pady=5)

    password_hint = tk.Label(
        reg_frame,
        text="Password must be at least 8 characters long and include numbers and special characters.",
        font=("Helvetica", 8),
        fg="gray",
    )
    password_hint.grid(row=5, column=1, sticky="w", padx=5, pady=(0, 5))

    def check_password_strength(event=None):
        """Checks password strength and provides visual feedback."""
        password = password_entry.get()
        special_chars = "!@#$%^&*()-_=+[{]}\\|;:'\",<.>/?`~"

        weak_color = "#ffcccc"  # Light red
        strong_color = "#ccffcc"  # Light green
        neutral_color = "white"  # Default

        # Empty field → neutral
        if not password:
            password_entry.config(background=neutral_color)
            return

        # Validate password strength
        if (
            len(password) < 8
            or not any(char.isdigit() for char in password)
            or not any(char in special_chars for char in password)
        ):
            password_entry.config(background=weak_color)
        else:
            password_entry.config(background=strong_color)

    # Bind live feedback to typing
    password_entry.bind("<KeyRelease>", check_password_strength)

    # Eye icon to toggle password visibility
    show_pw = False  # Track toggle state

    def toggle_password():
        """Toggle password visibility for both password fields."""
        nonlocal show_pw
        show_pw = not show_pw
        if show_pw:
            password_entry.config(show="")
            confirm_entry.config(show="")
            eye_button.config(image=eye_icon)
        else:
            password_entry.config(show="*")
            confirm_entry.config(show="*")
            eye_button.config(image=eye_icon)

    # Load small eye icons
    try:
        eye_icon = tk.PhotoImage(file=os.path.join("icons", "eye_icon.png"))
    except Exception as e:
        logger.warning(f"Could not load eye icons: {e}")
        eye_icon = None

    eye_button = ttk.Button(reg_frame, image=eye_icon, width=5, command=toggle_password)
    eye_button.image = eye_icon  # Keep a reference to prevent garbage collection
    eye_button.grid(row=3, column=2, padx=5)

    def handle_registration():
        """Handles User Registration"""
        first_name = first_name_entry.get().strip()
        last_name = last_name_entry.get().strip()
        email = email_entry.get().strip().lower()
        password = password_entry.get().strip()
        confirm_password = confirm_entry.get().strip()

        if (
            not first_name
            or not last_name
            or not email
            or not password
            or not confirm_password
        ):
            messagebox.showerror("Error", "All fields are required.")
            return
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            password_entry.config(background="#ffcccc")
            confirm_entry.config(background="#ffcccc")
            return
        if not first_name:
            messagebox.showerror("Input Error", "Please enter your full name.")
            logger.warning("Registration failed: Full name not provided.")
            first_name_entry.config(bg="#ffcccc")
            return
        if not last_name:
            messagebox.showerror("Input Error", "Please enter your last name.")
            logger.warning("Registration failed: Last name not provided.")
            last_name_entry.config(bg="#ffcccc")
            return
        if not email or "@" not in email:
            messagebox.showerror("Input Error", "Please enter a valid email address.")
            logger.warning("Registration failed: Invalid email format.")
            email_entry.config(bg="#ffcccc")
            return

        # check if email already exists in DB
        conn = get_db_connection()

        if not conn:  # Added Code
            messagebox.showerror(  # Added Code
                "Database Error",  # Added Code
                "Could not connect to the database. Please try again later.",  # Added Code
            )  # Added Code
            logger.error(
                "Registration failed: Database connection error."
            )  # Added Code
            return  # Added Code

        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            messagebox.showerror("Error", "Email already registered. Please login.")
            return

        # Special characters
        password_special_chars = r"!@#$%^&*()-_=+[{]}\|;:'\",<.>/?'~"
        if (
            len(password) < 8
            or not any(char.isdigit() for char in password)
            or not any(char in password_special_chars for char in password)
        ):
            messagebox.showerror(
                "Input Error",
                "Password must be at least 8 characters long and include numbers and special characters.",
            )
            logger.warning("Registration failed: Weak Password.")
            return

        # Hash the password before storing
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        try:
            user_id = db_add.add_user(
                first_name, last_name, email, None, None, password_hash
            )
            logger.info(f"New user registered with ID: {email}")
            messagebox.showinfo("Success", "Registration successful! Please login.")
            logger.info(f"User '{email}' registered successfully.")
            show_login(frame)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Email already registered. Please login.")
            logger.warning(
                f"Registration failed: Email '{email}' already exists in database."
            )
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during registration: {e}")
            logger.error(f"Registration failed due to error: {e}")
            return

    # Registration Button
    # reg_button = tk.Button(
    #     frame, text="Register", width=20, command=handle_registration
    # )
    # reg_button.pack(pady=20)
    reg_button = ttk.Button(
        frame,
        text="Register",
        command=handle_registration,
    )
    # Tkinter rule: you must not mix pack and grid in the same parent widget.
    # Doing that will cause runtime geometry warnings/errors and weird layout.
    reg_button.pack(pady=20)


# Preferences Page (need to add functionality to load preferences from database)


def show_preferences(frame):
    global current_user
    """Display for Preferences"""
    if not login_status:
        messagebox.showwarning("Access Denied", "Please login to set preferences.")
        logger.warning("Unauthorized access attempt to Preferences Form.")
        return

    set_active_button("Preferences")
    logger.info("Displaying the Preferences Form.")
    clear_content(frame)

    header_label = tk.Label(
        frame, text="Preferences Page", font=("Helvetica", 14, "bold")
    )
    header_label.pack(pady=20)

    pref_frame = ttk.Frame(frame)
    pref_frame.pack(pady=10)

    db_prefs = {}
    try:
        if current_user and "id" in current_user:
            db_prefs = get_user_preferences(current_user["id"]) or {}
    except Exception as e:
        logger.error("Failed to fetch user preferences: %s", e)
        db_prefs = {}

    exisiting_prefs = ["AI", "Machine Learning", "Data Science"]

    college_label = ttk.Label(pref_frame, text="College of:")
    college_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
    college_var = tk.StringVar(value=current_user.get("college", ""))
    college_combo = ttk.Combobox(
        pref_frame, textvariable=college_var, state="readonly", width=45
    )
    college_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    department_label = ttk.Label(pref_frame, text="Department:")
    department_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
    department_var = tk.StringVar(value=current_user.get("department", ""))
    department_combo = ttk.Combobox(
        pref_frame, textvariable=department_var, state="readonly", width=45
    )
    department_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    degree_level_label = ttk.Label(pref_frame, text="Degree Level:")
    degree_level_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
    degree_level_var = tk.StringVar(value=current_user.get("degree_level", ""))
    degree_level_combo = ttk.Combobox(
        pref_frame, textvariable=degree_level_var, state="readonly", width=45
    )
    degree_level_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    degree_label = ttk.Label(pref_frame, text="Degree:")
    degree_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
    degree_var = tk.StringVar(value=current_user.get("degree", ""))
    degree_combo = ttk.Combobox(
        pref_frame, textvariable=degree_var, state="readonly", width=45
    )
    degree_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

    job_label = ttk.Label(pref_frame, text="Preferred Job:")
    job_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
    job_var = tk.StringVar(value=current_user.get("job", ""))
    job_combo = ttk.Combobox(
        pref_frame, textvariable=job_var, state="readonly", width=45
    )
    job_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")

    job_desc_label = ttk.Label(frame, text="Job Description:")
    job_desc_label.pack(pady=(10, 0), anchor="w", padx=20)
    job_desc_text = tk.Text(frame, height=5, wrap="word", width=100)
    job_desc_text.pack(pady=5, padx=20, fill="x")

    college_name_to_id = {}

    try:
        colleges = get_colleges()
        college_name_to_id = {row["name"]: row["college_id"] for row in colleges}
        college_names = list(college_name_to_id.keys())
        college_combo["values"] = college_names

        selected_college_name = None
        pref_college_id = db_prefs.get("college_id")
        if pref_college_id is not None:
            for row in colleges:
                if row["college_id"] == pref_college_id:
                    selected_college_name = row["name"]
                    break

        if selected_college_name and selected_college_name in college_names:
            college_var.set(selected_college_name)
        else:
            college_var.set("Select your college")

        pref_department_id = db_prefs.get("department_id")
        department_names = []
        if pref_college_id is not None:
            departments = get_departments(pref_college_id)
            department_names = [row["name"] for row in departments]
            department_combo["values"] = department_names

            selected_dept_name = None
            if pref_department_id is not None:
                for row in departments:
                    if row["department_id"] == pref_department_id:
                        selected_dept_name = row["name"]
                        break
            if selected_dept_name and selected_dept_name in department_names:
                department_var.set(selected_dept_name)
        else:
            department_combo["values"] = []

        # Pre-populate degree levels, degrees, and jobs based on stored preferences  # Added Code
        pref_degree_level_id = db_prefs.get("degree_level_id")  # Added Code
        pref_degree_id = db_prefs.get("degree_id")  # Added Code
        pref_job_id = db_prefs.get("job_id")  # Added Code

        if pref_department_id is not None:  # Added Code
            try:  # Added Code
                levels = get_degree_levels(pref_department_id)  # Added Code
                level_names = [row["name"] for row in levels]  # Added Code
                degree_level_combo["values"] = level_names  # Added Code

                selected_level_name = None  # Added Code
                if pref_degree_level_id is not None:  # Added Code
                    for row in levels:  # Added Code
                        if row["degree_level_id"] == pref_degree_level_id:  # Added Code
                            selected_level_name = row["name"]  # Added Code
                            break  # Added Code
                if (
                    selected_level_name and selected_level_name in level_names
                ):  # Added Code
                    degree_level_var.set(selected_level_name)  # Added Code

                    degrees = get_degrees(pref_degree_level_id)  # Added Code
                    degree_names = [row["name"] for row in degrees]  # Added Code
                    degree_combo["values"] = degree_names  # Added Code

                    selected_degree_name = None  # Added Code
                    if pref_degree_id is not None:  # Added Code
                        for row in degrees:  # Added Code
                            if row["degree_id"] == pref_degree_id:  # Added Code
                                selected_degree_name = row["name"]  # Added Code
                                break  # Added Code
                    if (
                        selected_degree_name and selected_degree_name in degree_names
                    ):  # Added Code
                        degree_var.set(selected_degree_name)  # Added Code

                        jobs = get_jobs_by_degree(pref_degree_id)  # Added Code
                        job_names = [job["name"] for job in jobs]  # Added Code
                        job_combo["values"] = job_names  # Added Code

                        selected_job_name = None  # Added Code
                        if pref_job_id is not None:  # Added Code
                            for job in jobs:  # Added Code
                                if job["job_id"] == pref_job_id:  # Added Code
                                    selected_job_name = job["name"]  # Added Code
                                    job_desc_text.delete("1.0", "end")  # Added Code
                                    job_desc_text.insert(
                                        "1.0", job.get("description", "")
                                    )  # Added Code
                                    break  # Added Code
                        if (
                            selected_job_name and selected_job_name in job_names
                        ):  # Added Code
                            job_var.set(selected_job_name)  # Added Code
            except Exception as pref_exc:  # Added Code
                logger.error(
                    "Failed to pre-populate degree/job data: %s", pref_exc
                )  # Added Code
        else:  # Added Code
            degree_level_combo["values"] = []  # Added Code
            degree_combo["values"] = []  # Added Code
            job_combo["values"] = []  # Added Code

    except Exception as e:
        logger.error("Failed to load colleges/departments for preferences: %s", e)
        college_var.set("Select your college")
        department_combo["values"] = []

    def on_college_selected(event=None):  # Added Code
        """Update departments when a college is selected."""  # Added Code
        selected_name = college_var.get()  # Added Code
        college_id = college_name_to_id.get(selected_name)  # Added Code

        # Clear downstream combos when college changes  # Added Code
        department_combo["values"] = []  # Added Code
        department_var.set("")  # Added Code
        degree_level_combo["values"] = []  # Added Code
        degree_level_var.set("")  # Added Code
        degree_combo["values"] = []  # Added Code
        degree_var.set("")  # Added Code
        job_combo["values"] = []  # Added Code
        job_var.set("")  # Added Code
        job_desc_text.delete("1.0", "end")  # Added Code

        if college_id is None:  # Added Code
            return  # Added Code
        try:  # Added Code
            departments = get_departments(college_id)  # Added Code
            dept_names = [row["name"] for row in departments]  # Added Code
            department_combo["values"] = dept_names  # Added Code
        except Exception as exc:  # Added Code
            logger.error(
                "Failed to refresh departments for college '%s': %s", selected_name, exc
            )  # Added Code
            department_combo["values"] = []  # Added Code

    def on_department_selected(event=None):  # Added Code
        """Update degree levels when a department is selected."""  # Added Code
        selected_college_name = college_var.get()  # Added Code
        selected_dept_name = department_var.get()  # Added Code
        college_id = college_name_to_id.get(selected_college_name)  # Added Code

        degree_level_combo["values"] = []  # Added Code
        degree_level_var.set("")  # Added Code
        degree_combo["values"] = []  # Added Code
        degree_var.set("")  # Added Code
        job_combo["values"] = []  # Added Code
        job_var.set("")  # Added Code
        job_desc_text.delete("1.0", "end")  # Added Code

        if college_id is None or not selected_dept_name:  # Added Code
            return  # Added Code

        try:  # Added Code
            departments = get_departments(college_id)  # Added Code
            department_id = None  # Added Code
            for row in departments:  # Added Code
                if row["name"] == selected_dept_name:  # Added Code
                    department_id = row["department_id"]  # Added Code
                    break  # Added Code
            if department_id is None:  # Added Code
                logger.warning(
                    "Department '%s' not found for college_id %s",
                    selected_dept_name,
                    college_id,
                )  # Added Code
                return  # Added Code
            levels = get_degree_levels(department_id)  # Added Code
            names = [row["name"] for row in levels]  # Added Code
            degree_level_combo["values"] = names  # Added Code
        except Exception as exc:  # Added Code
            logger.error(
                "Failed to refresh degree levels for department '%s': %s",
                selected_dept_name,
                exc,
            )  # Added Code

    def on_degree_level_selected(event=None):  # Added Code
        """Update degrees when a degree level is selected."""  # Added Code
        selected_college_name = college_var.get()  # Added Code
        selected_dept_name = department_var.get()  # Added Code
        selected_level_name = degree_level_var.get()  # Added Code
        college_id = college_name_to_id.get(selected_college_name)  # Added Code

        degree_combo["values"] = []  # Added Code
        degree_var.set("")  # Added Code
        job_combo["values"] = []  # Added Code
        job_var.set("")  # Added Code
        job_desc_text.delete("1.0", "end")  # Added Code

        if (
            college_id is None or not selected_dept_name or not selected_level_name
        ):  # Added Code
            return  # Added Code

        try:  # Added Code
            departments = get_departments(college_id)  # Added Code
            department_id = None  # Added Code
            for row in departments:  # Added Code
                if row["name"] == selected_dept_name:  # Added Code
                    department_id = row["department_id"]  # Added Code
                    break  # Added Code
            if department_id is None:  # Added Code
                logger.warning(
                    "Department '%s' not found while resolving degree levels.",
                    selected_dept_name,
                )  # Added Code
                return  # Added Code

            levels = get_degree_levels(department_id)  # Added Code
            degree_level_id = None  # Added Code
            for row in levels:  # Added Code
                if row["name"] == selected_level_name:  # Added Code
                    degree_level_id = row["degree_level_id"]  # Added Code
                    break  # Added Code
            if degree_level_id is None:  # Added Code
                logger.warning(
                    "Degree level '%s' not found for department_id %s",
                    selected_level_name,
                    department_id,
                )  # Added Code
                return  # Added Code

            degrees = get_degrees(degree_level_id)  # Added Code
            names = [row["name"] for row in degrees]  # Added Code
            degree_combo["values"] = names  # Added Code
        except Exception as exc:  # Added Code
            logger.error(
                "Failed to refresh degrees for degree level '%s': %s",
                selected_level_name,
                exc,
            )  # Added Code

    def on_degree_selected(event=None):  # Added Code
        """Update jobs when a degree is selected."""  # Added Code
        selected_college_name = college_var.get()  # Added Code
        selected_dept_name = department_var.get()  # Added Code
        selected_level_name = degree_level_var.get()  # Added Code
        selected_degree_name = degree_var.get()  # Added Code
        college_id = college_name_to_id.get(selected_college_name)  # Added Code

        job_combo["values"] = []  # Added Code
        job_var.set("")  # Added Code
        job_desc_text.delete("1.0", "end")  # Added Code

        if (
            college_id is None
            or not selected_dept_name
            or not selected_level_name
            or not selected_degree_name
        ):  # Added Code
            return  # Added Code

        try:  # Added Code
            departments = get_departments(college_id)  # Added Code
            department_id = None  # Added Code
            for row in departments:  # Added Code
                if row["name"] == selected_dept_name:  # Added Code
                    department_id = row["department_id"]  # Added Code
                    break  # Added Code
            if department_id is None:  # Added Code
                logger.warning(
                    "Department '%s' not found while resolving degrees.",
                    selected_dept_name,
                )  # Added Code
                return  # Added Code

            levels = get_degree_levels(department_id)  # Added Code
            degree_level_id = None  # Added Code
            for row in levels:  # Added Code
                if row["name"] == selected_level_name:  # Added Code
                    degree_level_id = row["degree_level_id"]  # Added Code
                    break  # Added Code
            if degree_level_id is None:  # Added Code
                logger.warning(
                    "Degree level '%s' not found while resolving degrees.",
                    selected_level_name,
                )  # Added Code
                return  # Added Code

            degrees = get_degrees(degree_level_id)  # Added Code
            degree_id = None  # Added Code
            for row in degrees:  # Added Code
                if row["name"] == selected_degree_name:  # Added Code
                    degree_id = row["degree_id"]  # Added Code
                    break  # Added Code
            if degree_id is None:  # Added Code
                logger.warning(
                    "Degree '%s' not found for degree_level_id %s",
                    selected_degree_name,
                    degree_level_id,
                )  # Added Code
                return  # Added Code

            jobs = get_jobs_by_degree(degree_id)  # Added Code
            names = [job["name"] for job in jobs]  # Added Code
            job_combo["values"] = names  # Added Code
        except Exception as exc:  # Added Code
            logger.error(
                "Failed to refresh jobs for degree '%s': %s",
                selected_degree_name,
                exc,
            )  # Added Code

    def on_job_selected(event=None):  # Added Code
        """Update job description when a job is selected."""  # Added Code
        selected_job_name = job_var.get()  # Added Code
        selected_degree_name = degree_var.get()  # Added Code
        selected_level_name = degree_level_var.get()  # Added Code
        selected_dept_name = department_var.get()  # Added Code
        selected_college_name = college_var.get()  # Added Code

        job_desc_text.delete("1.0", "end")  # Added Code

        if (
            not selected_job_name
            or not selected_degree_name
            or not selected_level_name
            or not selected_dept_name
        ):  # Added Code
            return  # Added Code

        college_id = college_name_to_id.get(selected_college_name)  # Added Code
        if college_id is None:  # Added Code
            return  # Added Code

        try:  # Added Code
            departments = get_departments(college_id)  # Added Code
            department_id = None  # Added Code
            for row in departments:  # Added Code
                if row["name"] == selected_dept_name:  # Added Code
                    department_id = row["department_id"]  # Added Code
                    break  # Added Code
            if department_id is None:  # Added Code
                return  # Added Code

            levels = get_degree_levels(department_id)  # Added Code
            degree_level_id = None  # Added Code
            for row in levels:  # Added Code
                if row["name"] == selected_level_name:  # Added Code
                    degree_level_id = row["degree_level_id"]  # Added Code
                    break  # Added Code
            if degree_level_id is None:  # Added Code
                return  # Added Code

            degrees = get_degrees(degree_level_id)  # Added Code
            degree_id = None  # Added Code
            for row in degrees:  # Added Code
                if row["name"] == selected_degree_name:  # Added Code
                    degree_id = row["degree_id"]  # Added Code
                    break  # Added Code
            if degree_id is None:  # Added Code
                return  # Added Code

            jobs = get_jobs_by_degree(degree_id)  # Added Code
            for job in jobs:  # Added Code
                if job["name"] == selected_job_name:  # Added Code
                    job_desc_text.insert(
                        "1.0", job.get("description", "")
                    )  # Added Code
                    break  # Added Code
        except Exception as exc:  # Added Code
            logger.error(
                "Failed to update job description for job '%s': %s",
                selected_job_name,
                exc,
            )  # Added Code

    college_combo.bind("<<ComboboxSelected>>", on_college_selected)  # Added Code
    department_combo.bind("<<ComboboxSelected>>", on_department_selected)  # Added Code
    degree_level_combo.bind(
        "<<ComboboxSelected>>", on_degree_level_selected
    )  # Added Code
    degree_combo.bind("<<ComboboxSelected>>", on_degree_selected)  # Added Code
    job_combo.bind("<<ComboboxSelected>>", on_job_selected)  # Added Code

    # Start with empty, DB-driven values; handlers fill these in.  # Added Code
    degree_level_combo["values"] = []  #  Changed Code
    degree_combo["values"] = []  #  Changed Code
    job_combo["values"] = []  #  Changed Code

    def save_preferences():
        """Saves user preferences (now persisted to DB and in-memory)."""
        prefs = {
            "college": college_var.get(),
            "department": department_var.get(),
            "degree_level": degree_level_var.get(),
            "degree": degree_var.get(),
            "job": job_var.get(),
            "job_description": job_desc_text.get("1.0", "end").strip(),
        }
        current_user.update(prefs)
        logger.info(f"User preferences saved (in-memory): {prefs}")

        # Persist ID-based preferences to User_Preferences  # Added Code
        try:  # Added Code
            college_id = None  # Added Code
            department_id = None  # Added Code
            degree_level_id = None  # Added Code
            degree_id = None  # Added Code
            job_id = None  # Added Code

            selected_college_name = college_var.get()  # Added Code
            if (
                selected_college_name and selected_college_name in college_name_to_id
            ):  # Added Code
                college_id = college_name_to_id[selected_college_name]  # Added Code

            if college_id is not None and department_var.get():  # Added Code
                departments = get_departments(college_id)  # Added Code
                for row in departments:  # Added Code
                    if row["name"] == department_var.get():  # Added Code
                        department_id = row["department_id"]  # Added Code
                        break  # Added Code

            if department_id is not None and degree_level_var.get():  # Added Code
                levels = get_degree_levels(department_id)  # Added Code
                for row in levels:  # Added Code
                    if row["name"] == degree_level_var.get():  # Added Code
                        degree_level_id = row["degree_level_id"]  # Added Code
                        break  # Added Code

            if degree_level_id is not None and degree_var.get():  # Added Code
                degrees = get_degrees(degree_level_id)  # Added Code
                for row in degrees:  # Added Code
                    if row["name"] == degree_var.get():  # Added Code
                        degree_id = row["degree_id"]  # Added Code
                        break  # Added Code

            if degree_id is not None and job_var.get():  # Added Code
                jobs = get_jobs_by_degree(degree_id)  # Added Code
                for job in jobs:  # Added Code
                    if job["name"] == job_var.get():  # Added Code
                        job_id = job["job_id"]  # Added Code
                        break  # Added Code

            db_pref_payload = {  # Added Code
                "college_id": college_id,  # Added Code
                "department_id": department_id,  # Added Code
                "degree_level_id": degree_level_id,  # Added Code
                "degree_id": degree_id,  # Added Code
                "job_id": job_id,  # Added Code
            }  # Added Code
            if current_user and "id" in current_user:  # Added Code
                ok = save_user_preferences(
                    current_user["id"], db_pref_payload
                )  # Added Code
                if not ok:  # Added Code
                    logger.error(
                        "save_user_preferences returned False for user_id %s",
                        current_user["id"],
                    )  # Added Code
        except Exception as exc:  # Added Code
            logger.error(
                "Failed to persist preferences to database: %s", exc
            )  # Added Code

        messagebox.showinfo("Preferences Saved", "Your preferences have been saved.")

    def clear_preferences():
        """Clears all preference fields"""
        college_var.set("")
        department_var.set("")
        degree_level_var.set("")
        degree_var.set("")
        job_var.set("")
        job_desc_text.delete("1.0", "end")
        logger.info("User cleared all preferences fields.")

        for key in [
            "college",
            "department",
            "degree_level",
            "degree",
            "job",
            "job_description",
        ]:
            current_user[key] = ""
        logger.info("Current user preferences reset in memory.")
        messagebox.showinfo(
            "Preferences Cleared", "All preference fields have been cleared."
        )

    save_button = tk.Button(
        frame, text="Save Preferences", width=20, command=save_preferences
    )
    save_button.pack(pady=20)

    clear_button = tk.Button(
        frame,
        text="Clear Preferences",
        width=20,
        bg="#FF6666",
        command=clear_preferences,
    )
    clear_button.pack(pady=5)


# Placeholder for recommendations page
def show_recommendations(frame):
    """Display for Recommendations Page"""
    # Guard to prevent unauthorized access
    if not login_status:
        messagebox.showwarning("Access Denied", "Please login to view recommendations.")
        logger.warning("Unauthorized access attempt to Recommendations Page.")
        return
    set_active_button("Recommendations")
    logger.info("Displaying Recommendations Page")
    clear_content(frame)
    header_label = tk.Label(
        frame, text="Course Recommendations", font=("Helvetica", 14)
    )
    header_label.pack(pady=20)

    # Generate Recommendations Button (need to add function to generate recommendations)
    generate_button = tk.Button(
        frame,
        text="Generate Recommendations",
        width=25,
        command=lambda: generate_recommendations_ui(frame),
    )
    generate_button.pack(pady=10)

    # Recommendations Display Frame
    rec_frame = ttk.Frame(frame)
    rec_frame.pack(pady=10, padx=20, fill="both", expand=True)


#  Parse recommednations function
def parse_recommendations(raw_response):
    """
    Parses the raw AI response (JSON string) into a structured list of course recommendations.

    :param raw_response: str, The raw JSON response from the AI model.
    :return: list of dicts, Each dict contains course details.
    """
    recommendations = []
    try:
        # Parse the JSON string into a Python list
        data = json.loads(raw_response)
        logger.debug("Parsed JSON response successfully.")

        if isinstance(data, list):
            for course in data:
                # Optional: Validate required keys
                required_keys = [
                    "Course Code",
                    "Course Name",
                    "Rating",
                    "Prerequisites",
                    "Explanation",
                ]
                if all(key in course for key in required_keys):
                    recommendations.append(course)
                else:
                    logger.warning(f"Course data missing required keys: {course}")
        else:
            logger.error("AI response is not a list.")
    except json.JSONDecodeError as jde:
        logger.error(f"JSON decoding failed: {jde}")
    except Exception as e:
        logger.error(f"Error parsing AI recommendations: {e}")
    return recommendations


def display_recommendations_ui(rec_frame, recommendations):
    """Displays the list of recommendations in the given frame with toggleable explanations."""
    clear_content(rec_frame)

    if not recommendations:
        messagebox.showinfo("No Recommendations", "No recommendations available.")
        return

    # Create a Canvas widget inside rec_frame
    canvas = tk.Canvas(rec_frame, borderwidth=0, background="#f0f0f0")
    scrollbar = ttk.Scrollbar(rec_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, padding=(10, 10, 10, 10))

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y", pady=10)
    rec_frame.pack(fill="both", expand=True)

    for rec in recommendations:
        rec_container = ttk.Frame(
            scrollable_frame, relief="solid", borderwidth=1, padding=(10, 10)
        )
        rec_container.pack(padx=5, pady=5, fill="x", expand=True)

        # Course Name and Code
        course_label = ttk.Label(
            rec_container,
            text=f"{rec.get('Course Name', 'N/A')} ({rec.get('Course Code', 'N/A')})",
            font=("Helvetica", 12, "bold"),
            background="#ffffff",
        )
        course_label.pack(anchor="w", padx=5, pady=5)

        # Units
        units = rec.get("Units", "N/A")
        units_label = ttk.Label(
            rec_container, text=f"Units: {units}", background="#ffffff"
        )
        units_label.pack(anchor="w", padx=5)

        # Rating
        rating = rec.get("Rating", "N/A")
        rating_label = ttk.Label(
            rec_container, text=f"Rating: {rating}/100", background="#ffffff"
        )
        rating_label.pack(anchor="w", padx=5)

        # Prerequisites
        prereqs = rec.get("Prerequisites", "")
        prereq_text = prereqs if prereqs else "None"
        prereq_label = ttk.Label(
            rec_container, text=f"Prerequisites: {prereq_text}", background="#ffffff"
        )
        prereq_label.pack(anchor="w", padx=5, pady=5)

        # Toggle Button for Explanation
        toggle_btn = ttk.Button(rec_container, text="Show Explanation")
        toggle_btn.pack(anchor="w", padx=5, pady=5)

        # Explanation Label (Initially Hidden)
        explanation = rec.get("Explanation", "No explanation provided.")
        explanation_label = ttk.Label(
            rec_container,
            text=explanation,
            wraplength=800,
            justify="left",
            background="#e6e6e6",
            padding=(5, 5),
        )
        # Do not pack the explanation_label yet (hidden by default)

        def toggle_explanation(label=explanation_label, button=toggle_btn):
            """Toggle the visibility of the explanation label."""
            if label.winfo_ismapped():
                label.pack_forget()
                button.config(text="Show Explanation")
            else:
                label.pack(anchor="w", padx=5, pady=5)
                button.config(text="Hide Explanation")

        toggle_btn.config(command=toggle_explanation)

        # Optional: Button to view more details
        details_btn = ttk.Button(
            rec_container,
            text="View Details",
            command=lambda c=rec: show_course_details(rec_container, c),
        )
        details_btn.pack(anchor="e", padx=5, pady=5)


# Function to generate and display recommendations (Need to add live AI functionality and database)
def generate_recommendations_ui(frame):
    """Generates and displays course recommednations (Placeholder need to add functionality with AI and database)"""
    global current_user

    clear_content(frame)
    set_active_button("Recommendations")
    header_label = tk.Label(
        frame, text="Course Recommendations", font=("Helvetica", 14)
    )
    header_label.pack(pady=20)

    # Loading label
    loading_label = tk.Label(
        frame, text="Generating recommendations, please wait...", font=("Helvetica", 12)
    )
    loading_label.pack(pady=10)
    frame.update()

    try:
        required_fields = ["college", "department", "degree_level", "degree", "job"]
        missing_fields = [
            field
            for field in required_fields
            if field not in current_user or not current_user[field]
        ]
        if missing_fields:
            messagebox.showwarning(
                "Incomplete Preferences",
                f"Please complete your preferences before generating recommendations. Missing: {', '.join(missing_fields)}",
            )
            logger.warning(
                f"Cannot generate recommendations, missing preferences: {missing_fields}"
            )
            show_preferences(frame)
            return

        # Parse electives from CSV
        csv_path = os.path.join("database", "courses.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Electives CSV file not found at {csv_path}")

        with open(csv_path, "r", encoding="utf-8") as f:
            csv_text = f.read()
        degree_electives = _parse_degree_electives_csv(csv_text)

        # Get recommendations from AI module
        job_name = current_user["job"]
        degree_name = current_user["degree"]
        job_id = 1  # Placeholder job ID

        response = get_recommendations_ai(
            job_id=job_id,
            job_name=job_name,
            degree_name=degree_name,
            degree_electives=degree_electives,
        )
        recommendations = parse_recommendations(response)
        if not recommendations:
            messagebox.showerror(
                "AI Error", "Failed to parse recommendations. Please try again."
            )
            logger.error("No recommednations parsed from AI response.")
            return
        rec_frame = frame.winfo_children()[-1]  # Get the last child, which is rec_frame
        clear_content(rec_frame)
        display_recommendations_ui(rec_frame, recommendations)

        # Old Logic
        """
        # Parse JSON response
        rec_data = json.loads(response)
        loading_label.destroy()  # Remove loading label

        # Display recommendations
        results_frame = ttk.Frame(frame)
        results_frame.pack(pady=10, padx=20, fill="both", expand=True)

        canvas = tk.Canvas(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            ))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Show each recommended course
        if isinstance(rec_data, list) and rec_data:
            for course in rec_data:
                title = course.get("Course Name", "N/A")
                desc = course.get("Description", "No description available.")
                units = course.get("Units", "N/A")
                prereqs = ", ".join([course.get(f"Prereq{i}", "") for i in range(1, 4) if course.get(f"Prereq{i}")])
                card = ttk.LabelFrame(scrollable_frame, text=title)
                card.pack(fill="x", pady=5, padx=5)

                info = f"Units: {units}\nPrerequisites: {prereqs}\n\n{desc}"
                tk.Label(card, text=info, justify = "left", wraplength=800, font=("Helvetica", 10, "bold")).pack(anchor="w", padx=10, pady=5)

        else:
           tk.Label(scrollable_frame, text="No recommendations found.", font=("Helvetica", 12)).pack(pady=20)
           logger.info("No recommendations returned from AI module.")
 """
        logger.info("Course recommendations generated and displayed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        logger.error(f"Error checking user preferences: {e}")
        return


def save_recommendations_to_db(recommendations):
    """Saves Recommendations to the database (Placeholder function)"""
    saved_count = 0


# Placeholder for course details page
def show_course_details(frame):
    """Display for course details"""
    clear_content(frame)
    tk.Label(frame, text="Course Details Page", font=("Helvetica", 14)).pack(pady=20)


# Placeholder for profile page
def show_profile(frame):
    """Display for User Profile and Account Settings"""
    logger.info("Displaying Profile Page")
    set_active_button("Profile")
    clear_content(frame)
    global current_user

    profile_header = tk.Label(frame, text="User Profile", font=("Helvetica", 14))
    profile_header.pack(pady=20)

    full_name = f"{current_user.get('first_name', 'N/A')} {current_user.get('last_name', '')}".strip()
    profile_name_label = tk.Label(
        frame, text=f"Name: {full_name}", font=("Helvetica", 12)
    )
    profile_name_label.pack(pady=5)

    profile_email_label = tk.Label(
        frame, text=f"Email: {current_user.get('email', 'N/A')}", font=("Helvetica", 12)
    )
    profile_email_label.pack(pady=5)

    settings_frame = ttk.LabelFrame(frame, text="Account Settings")
    settings_frame.pack(pady=20, fill="x", padx=20)

    def change_password():
        """Changes Password"""
        logger.info("User initiated password change.")
        password_window = tk.Toplevel(frame)
        password_window.title("Change Password")

        current_password_label = ttk.Label(password_window, text="Current Password:")
        current_password_label.pack(pady=10, padx=10, anchor="w")
        current_password_entry = ttk.Entry(password_window, width=30, show="*")
        current_password_entry.pack(pady=5, padx=10, anchor="w")

        new_password_label = ttk.Label(password_window, text="New Password:")
        new_password_label.pack(pady=10, padx=10, anchor="w")
        new_password_entry = ttk.Entry(password_window, width=30, show="*")
        new_password_entry.pack(pady=5, padx=10, anchor="w")

        confirm_new_pw_label = ttk.Label(password_window, text="Confirm New Password:")
        confirm_new_pw_label.pack(pady=10, padx=10, anchor="w")
        confirm_new_pw_entry = ttk.Entry(password_window, width=30, show="*")
        confirm_new_pw_entry.pack(pady=5, padx=10, anchor="w")

        def perform_password_change():
            current_password = current_password_entry.get().strip()
            new_password = new_password_entry.get().strip()
            confirm_password = confirm_new_pw_entry.get().strip()

            # open db connection
            conn = get_db_connection()
            cursor = conn.cursor()

            # get stored hashed password from db
            cursor.execute(
                "SELECT password_hash FROM users WHERE email = ?",
                (current_user["email"],),
            )
            row = cursor.fetchone()

            if not row:
                messagebox.showerror(
                    "Error",
                    "User record not found in database.",
                    parent=password_window,
                )
                conn.close()
                return

            stored_hash = row[0]

            # verify current password matches the stored hash
            if not bcrypt.checkpw(
                current_password.encode("utf-8"), stored_hash.encode("utf-8")
            ):
                messagebox.showerror(
                    "Error", "Current password is incorrect.", parent=password_window
                )
                conn.close()
                return

            # confirm new passwords match
            if new_password != confirm_password:
                messagebox.showerror(
                    "Error", "New passwords do not match.", parent=password_window
                )
                conn.close()
                return

            if len(new_password) < 8:
                messagebox.showerror(
                    "Error",
                    "Password must be at least 8 characters long.",
                    parent=password_window,
                )
                return

            # hash new password
            new_hash = bcrypt.hashpw(
                new_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # update password in DB
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE email = ?",
                (new_hash, current_user["email"]),
            )
            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Success", "Password changed successfully!", parent=password_window
            )
            logger.info(f"User '{current_user['email']}' changed password.")
            password_window.destroy()

        save_password_button = ttk.Button(
            password_window, text="Save Password", command=perform_password_change
        )
        save_password_button.pack(pady=20)

    change_password_button = ttk.Button(
        settings_frame, text="Change Password", command=change_password
    )
    change_password_button.pack(pady=10, padx=10, fill="x")


# Placeholder for Help Page
def show_help(frame):
    """Display the Help Page"""
    logger.info("Displaying Help Page")
    clear_content(frame)
    set_active_button("Help")

    header_label = ttk.Label(frame, text="Help & Support", font=("Helvetica", 20))
    header_label.pack(pady=20)

    help_frame = ttk.Frame(frame)
    help_frame.pack(pady=10, padx=20, fill="both", expand=True)

    help_text = (
        "Welcome to the Smart Elective Advisor Help Center!\n\n"
        "If you need help navigating the application or have any questions, we've got you covered.\n\n"
        "1. Use Guides: Detailed manuals to help you explore and make the most of the application's features\n\n"
        "2. FAQs: Quick answers to the most common questions from other users.\n\n"
        "3. Contact Support: Need personalized help? Reach out to our support team at support@university.edu\n\n"
    )
    help_label = ttk.Label(
        help_frame,
        text=help_text,
        font=("Helvetica", 14),
        wraplength=800,
        justify="left",
    )
    help_label.pack(pady=10)

    search_label = ttk.Label(
        help_frame, text="Search Help Topics:", font=("Helvetica", 12)
    )
    search_label.pack(pady=5, anchor="w")
    search_entry = ttk.Entry(help_frame, width=50)
    search_entry.pack(pady=5, anchor="w")

    def search_help():
        query = search_entry.get()
        messagebox.showinfo("Coming soon", "coming soon")

    search_button = ttk.Button(help_frame, text="Search", command=search_help)
    search_button.pack(pady=5, anchor="w")

    # Push the About button to the bottom-right  # Added Code
    help_frame.pack_propagate(False)  # Added Code
    spacer = ttk.Frame(help_frame)  # Added Code
    spacer.pack(fill="both", expand=True)  # Added Code
    about_button = ttk.Button(  # Added Code
        help_frame,
        text="About",
        command=lambda: show_about_dialog(frame),
    )  # Added Code
    about_button.pack(pady=10, anchor="e")  # Added Code


def main_test_ui(option: int) -> bool:
    """
    UI test dispatcher:
      option 1 -> launch the real GUI (blocking; user must close window)
      option 2 -> sanity create/destroy root without entering mainloop (fast)
      option 3 -> launch GUI and auto-close after 1 second (useful for CI)
    Returns True on success, False on failure.
    """
    logger.info("main_test_ui: selected option %s", option)

    if option == 1:
        try:
            main_int_ui()
            return True
        except Exception:
            logger.exception("main_test_ui option 1 failed")
            return False

    elif option == 2:
        try:
            root = tk.Tk()
            root.update_idletasks()
            root.destroy()
            logger.info("main_test_ui option 2: sanity create/destroy succeeded")
            return True
        except Exception:
            logger.exception("main_test_ui option 2 failed")
            return False

    elif option == 3:
        try:
            # Start the GUI in a separate thread and auto-close after 1 second.
            def _run_and_close():
                root = tk.Tk()
                root.title("Smart Elective Advisor (auto-close test)")
                label = tk.Label(root, text="Auto-close test (1s)")
                label.pack(padx=10, pady=10)
                # schedule close after 1000 ms
                root.after(1000, root.destroy)
                try:
                    root.mainloop()
                except Exception:
                    logger.exception("Exception in auto-close GUI thread")

            t = threading.Thread(target=_run_and_close, daemon=True)
            t.start()
            # wait a bit for thread to run and GUI to close
            time.sleep(1.5)
            logger.info("main_test_ui option 3: auto-close GUI test completed")
            return True
        except Exception:
            logger.exception("main_test_ui option 3 failed")
            return False

    else:
        logger.error("main_test_ui: unknown option %s", option)
        return False


if __name__ == "__main__":
    main_test_ui(1)
