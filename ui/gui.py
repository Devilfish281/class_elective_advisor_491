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
from PIL import Image, ImageTk

from ai_integration.ai_module import (  # AI integration
    _parse_degree_electives_csv, get_recommendations_ai)
from database import db_add  # For database interactions
from database import db_operations  # Importing db_operations for authenticatio
from database.db_operations import (get_colleges, get_degree_levels,
                                    get_degrees, get_departments,
                                    get_jobs_by_degree, get_user_preferences,
                                    save_user_preferences)
from ui import theme  # NEW: TitanPark-themed colors and styles
# Import About dialog
from ui.app_version import show_about_dialog
from ui.gui_titanpark_integration import (show_parking_helper,
                                          show_parking_history_helper)

logger = logging.getLogger(__name__)  # Reuse the global logger

# --- TitanPark-inspired theme (NEW) ---
TP_BG = "#020814"  # dark background
TP_SIDEBAR_BG = "#050B18"  # sidebar background
TP_CARD_BG = "#101827"  # card / panel background
TP_ACCENT = "#FF7900"  # accent orange
TP_TEXT_PRIMARY = "#F9FAFB"
TP_TEXT_MUTED = "#9CA3AF"

# Use the same family name as your TitanPark Flutter app here.
# If the font is not installed, Tk will fall back gracefully.
TP_FONT_FAMILY = "Museo Sans"  # change to your actual font name if different

BASE_FONT = (TP_FONT_FAMILY, 11)
HEADER_FONT = (TP_FONT_FAMILY, 16, "bold")
SUBHEADER_FONT = (TP_FONT_FAMILY, 13, "bold")


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

    # Minimal Tkinter window (UPDATED STYLING)
    root = tk.Tk()
    theme.init_fonts(root)
    theme.apply_root_theme(root)
    root.title("Smart Elective Advisor with TitanPark")
    root.geometry("1200x800")
    root.configure(bg=TP_BG)  # New dark background

    # Grid Layout
    root.columnconfigure(0, weight=0)  # Navigation Menu
    root.columnconfigure(1, weight=1)  # Content Display
    root.rowconfigure(0, weight=1)

    # Create Navigation Menu Frame (UPDATED COLORS)
    nav_frame = tk.Frame(
        root,
        width=250,
        relief="flat",
        bg=TP_SIDEBAR_BG,
    )
    nav_frame.grid(row=0, column=0, sticky="ns")
    nav_frame.grid_propagate(False)
    nav_frame.columnconfigure(0, weight=1)
    theme.style_sidebar_frame(nav_frame)  # NEW: TitanPark sidebar styling

    # Content Area (UPDATED COLORS)
    content_frame = tk.Frame(
        root,
        bg=TP_BG,
        relief="flat",
        bd=0,
    )

    content_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    content_frame.set_active_button = set_active_button
    theme.style_main_frame(content_frame)  # NEW: TitanPark content background

    # Styles for sidebar buttons (UPDATED FOR TITANPARK LOOK)
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "TButton",
        padding=10,
        anchor="w",
        font=BASE_FONT,
        background=TP_SIDEBAR_BG,
        foreground=TP_TEXT_MUTED,
    )
    style.map(
        "TButton",
        background=[
            ("pressed", TP_ACCENT),
            ("active", TP_ACCENT),
        ],
        foreground=[
            ("pressed", TP_TEXT_PRIMARY),
            ("active", TP_TEXT_PRIMARY),
        ],
    )

    style.configure(
        "Active.TButton",
        padding=10,
        anchor="w",
        font=(TP_FONT_FAMILY, 11, "bold"),
        background=TP_ACCENT,
        foreground=TP_TEXT_PRIMARY,
    )

    theme.init_sidebar_styles(style)  # NEW: TitanPark button styles

    # Status bar at the bottom
    global status_var
    status_var = tk.StringVar()
    status_var.set("Not logged in")

    status_bar = tk.Label(
        root,
        textvariable=status_var,
        bd=0,
        relief="flat",
        anchor="w",
        bg=TP_SIDEBAR_BG,
        fg=TP_TEXT_MUTED,
        font=BASE_FONT,
    )

    status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
    theme.style_status_bar(status_bar)  # NEW: Titan-style status bar

    # Helps show orange highlight on active button
    def show_parking(frame):
        set_active_button("Parking")
        show_parking_helper(frame)

    # Menu Items
    menu_items = [
        ("Home", "icons/home.png", show_home),
        ("Login", "icons/login.png", show_login),
        ("Logout", "icons/logout.png", show_logout),
        ("Registration", "icons/register.png", show_registration),
        ("Preferences", "icons/preferences.png", show_preferences),
        ("Recommendations", "icons/recommendations.png", show_recommendations),
        ("Profile", "icons/profile.png", show_profile),
        ("Parking", "icons/parking.png", show_parking),  
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
    theme.style_main_frame(frame)

    card = tk.Frame(
        frame,
        bg=theme.CARD_BG,
        bd=0,
        highlightthickness=1,
        highlightbackground=theme.CARD_BORDER,
    )
    card.pack(padx=40, pady=60, fill="x")

    label = tk.Label(
        card,
        text="Welcome to Smart Elective Advisor with TitanPark",
        font=(TP_FONT_FAMILY, 18, "bold"),
        bg=theme.CARD_BG,
        fg=theme.TEXT_PRIMARY,
    )
    label.pack(padx=24, pady=(20, 8), anchor="w")

    info_text = (
        "The Smart Elective Advisor helps CS students select the best elective courses based on their "
        "interests, career aspirations, and academic performance. Navigate through the menu to get started."
    )
    info = tk.Label(
        card,
        text=info_text,
        wraplength=700,
        justify="left",
        bg=theme.CARD_BG,
        fg=theme.TEXT_MUTED,
        font=theme.FONT_BODY,
    )
    info.pack(padx=24, pady=(0, 12), anchor="w")

    # Merger banner image (loads AFTER Tk root exists)
    try:
        img_path = os.path.join("ui", "assets", "titanpark_merge_message.png")
        pil_img = Image.open(img_path)

        # Resize to fit the card width nicely
        target_w = 700
        w, h = pil_img.size
        scale = target_w / float(w)
        pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        merge_img = ImageTk.PhotoImage(pil_img, master=frame.winfo_toplevel())

        merge_img_label = tk.Label(card, image=merge_img, bg=theme.CARD_BG)
        merge_img_label.image = merge_img  # prevent garbage collection
        merge_img_label.pack(padx=24, pady=(0, 12), anchor="w")

    except Exception as e:
        logger.warning(f"Could not load merge image: {e}")


# Login Page
def show_login(frame):
    """Displays the Login Page."""
    set_active_button("Login")
    clear_content(frame)

    # Centered card container for the login form (NEW)
    card_frame = tk.Frame(
        frame,
        bg=TP_CARD_BG,  # dark card background
        bd=0,
        highlightbackground="#1F2937",  # subtle border
        highlightthickness=1,
        padx=40,
        pady=30,
    )
    card_frame.pack(pady=80)  # center the card vertically

    header_label = tk.Label(
        card_frame,
        text="Login Page",
        font=HEADER_FONT,
        bg=TP_CARD_BG,
        fg=TP_TEXT_PRIMARY,
        bd=0,
        highlightthickness=0,
        relief="flat",
    )
    header_label.pack(pady=10)

    # Email
    email_label = tk.Label(
        card_frame,
        text="Email:",
        bg=TP_CARD_BG,
        fg=TP_TEXT_PRIMARY,
        font=BASE_FONT,
    )
    email_label.pack(pady=(10, 5))
    email_entry = tk.Entry(
        card_frame,
        width=30,
        bg=TP_BG,  # inner field background
        fg=TP_TEXT_PRIMARY,
        insertbackground=TP_TEXT_PRIMARY,
        bd=0,
        highlightthickness=0,
        font=BASE_FONT,
    )
    email_entry.pack(pady=(0, 10))

    # Password
    password_label = tk.Label(
        card_frame,
        text="Password:",
        bg=TP_CARD_BG,
        fg=TP_TEXT_PRIMARY,
        font=BASE_FONT,
    )
    password_label.pack(pady=(10, 5))
    # Frame to hold password entry and eye icon
    pw_frame = tk.Frame(card_frame, bg=TP_CARD_BG)  # keep same card bg
    pw_frame.pack(pady=(0, 10))

    password_entry = tk.Entry(
        pw_frame,
        width=30,
        show="*",
        bg=TP_BG,  # inner field bg
        fg=TP_TEXT_PRIMARY,
        insertbackground=TP_TEXT_PRIMARY,
        bd=0,
        highlightthickness=0,
        font=BASE_FONT,
    )
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

    # Make the eye icon sit on a lighter navy chip so it is visible on dark backgrounds
    eye_button = tk.Button(
        pw_frame,
        image=eye_icon,
        width=24,
        height=24,
        command=toggle_password,
        bg="#1F2937",  # lighter navy so the dark eye stands out
        activebackground="#1F2937",
        relief="flat",
        bd=0,
    )
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
    login_button = tk.Button(
        card_frame,
        text="Login",
        width=15,
        command=handle_login,
        bg="#D9D9D9",
        fg="#0A1931",  # <-- NEW: TitanPark dark blue text
        activebackground=TP_ACCENT,
        activeforeground=TP_TEXT_PRIMARY,
        bd=0,
        font=BASE_FONT,
    )
    login_button.pack(pady=(20, 10))

    # Forgot password link
    forgot_password_label = tk.Label(
        card_frame,
        text="Forgot password?",
        fg="#3B82F6",  # Titan-ish blue link
        cursor="hand2",
        bg=TP_CARD_BG,
        font=BASE_FONT,
    )
    forgot_password_label.pack(pady=(5, 2))
    forgot_password_label.bind("<Button-1>", lambda e: show_forgot_password(frame))

    # Registration link
    reg_label = tk.Label(
        card_frame,
        text="Don't have an account? Register",
        fg="#3B82F6",
        cursor="hand2",
        bg=TP_CARD_BG,
        font=BASE_FONT,
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

    tk.Label(popup, text="Reset Your Password", font=(TP_FONT_FAMILY, 14, "bold")).pack(
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
    theme.style_main_frame(frame)  # NEW: TitanPark background for registration
    header_label = tk.Label(
        frame, text="User Registration", font=(TP_FONT_FAMILY, 20, "bold")
    )
    header_label.configure(bg=theme.CONTENT_BG, fg=theme.TEXT_PRIMARY)
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
        font=(TP_FONT_FAMILY, 8),
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

    # Same lighter navy chip for the registration eye icon so it stays visible
    eye_button = tk.Button(
        reg_frame,
        image=eye_icon,
        width=24,
        height=24,
        command=toggle_password,
        bg="#1F2937",
        activebackground="#1F2937",
        relief="flat",
        bd=0,
    )
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

        if not conn:
            messagebox.showerror(
                "Database Error",
                "Could not connect to the database. Please try again later.",
            )
            logger.error("Registration failed: Database connection error.")
            return

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
    reg_button = tk.Button(  # NEW: TitanPark-style registration button
        frame,
        text="Register",
        command=handle_registration,
    )
    reg_button.configure(
        bg=theme.ACCENT_BLUE,
        fg="white",
        activebackground="#1E40AF",
        activeforeground="white",
        relief="flat",
        borderwidth=0,
        padx=16,
        pady=8,
        font=(TP_FONT_FAMILY, 11, "bold"),
        cursor="hand2",
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
        frame, text="Preferences Page", font=(TP_FONT_FAMILY, 14, "bold")
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

        # Pre-populate degree levels, degrees, and jobs based on stored preferences
        pref_degree_level_id = db_prefs.get("degree_level_id")
        pref_degree_id = db_prefs.get("degree_id")
        pref_job_id = db_prefs.get("job_id")

        if pref_department_id is not None:
            try:
                levels = get_degree_levels(pref_department_id)
                level_names = [row["name"] for row in levels]
                degree_level_combo["values"] = level_names

                selected_level_name = None
                if pref_degree_level_id is not None:
                    for row in levels:
                        if row["degree_level_id"] == pref_degree_level_id:
                            selected_level_name = row["name"]
                            break
                if selected_level_name and selected_level_name in level_names:
                    degree_level_var.set(selected_level_name)

                    degrees = get_degrees(pref_degree_level_id)
                    degree_names = [row["name"] for row in degrees]
                    degree_combo["values"] = degree_names

                    selected_degree_name = None
                    if pref_degree_id is not None:
                        for row in degrees:
                            if row["degree_id"] == pref_degree_id:
                                selected_degree_name = row["name"]
                                break
                    if selected_degree_name and selected_degree_name in degree_names:
                        degree_var.set(selected_degree_name)

                        jobs = get_jobs_by_degree(pref_degree_id)
                        job_names = [job["name"] for job in jobs]
                        job_combo["values"] = job_names

                        selected_job_name = None
                        if pref_job_id is not None:
                            for job in jobs:
                                if job["job_id"] == pref_job_id:
                                    selected_job_name = job["name"]
                                    job_desc_text.delete("1.0", "end")
                                    job_desc_text.insert(
                                        "1.0", job.get("description", "")
                                    )
                                    break
                        if selected_job_name and selected_job_name in job_names:
                            job_var.set(selected_job_name)
            except Exception as pref_exc:
                logger.error("Failed to pre-populate degree/job data: %s", pref_exc)
        else:
            degree_level_combo["values"] = []
            degree_combo["values"] = []
            job_combo["values"] = []

    except Exception as e:
        logger.error("Failed to load colleges/departments for preferences: %s", e)
        college_var.set("Select your college")
        department_combo["values"] = []

    def on_college_selected(event=None):
        """Update departments when a college is selected."""
        selected_name = college_var.get()
        college_id = college_name_to_id.get(selected_name)

        # Clear downstream combos when college changes
        department_combo["values"] = []
        department_var.set("")
        degree_level_combo["values"] = []
        degree_level_var.set("")
        degree_combo["values"] = []
        degree_var.set("")
        job_combo["values"] = []
        job_var.set("")
        job_desc_text.delete("1.0", "end")

        if college_id is None:
            return
        try:
            departments = get_departments(college_id)
            dept_names = [row["name"] for row in departments]
            department_combo["values"] = dept_names
        except Exception as exc:
            logger.error(
                "Failed to refresh departments for college '%s': %s", selected_name, exc
            )
            department_combo["values"] = []

    def on_department_selected(event=None):
        """Update degree levels when a department is selected."""
        selected_college_name = college_var.get()
        selected_dept_name = department_var.get()
        college_id = college_name_to_id.get(selected_college_name)

        degree_level_combo["values"] = []
        degree_level_var.set("")
        degree_combo["values"] = []
        degree_var.set("")
        job_combo["values"] = []
        job_var.set("")
        job_desc_text.delete("1.0", "end")

        if college_id is None or not selected_dept_name:
            return

        try:
            departments = get_departments(college_id)
            department_id = None
            for row in departments:
                if row["name"] == selected_dept_name:
                    department_id = row["department_id"]
                    break
            if department_id is None:
                logger.warning(
                    "Department '%s' not found for college_id %s",
                    selected_dept_name,
                    college_id,
                )
                return
            levels = get_degree_levels(department_id)
            names = [row["name"] for row in levels]
            degree_level_combo["values"] = names
        except Exception as exc:
            logger.error(
                "Failed to refresh degree levels for department '%s': %s",
                selected_dept_name,
                exc,
            )

    def on_degree_level_selected(event=None):
        """Update degrees when a degree level is selected."""
        selected_college_name = college_var.get()
        selected_dept_name = department_var.get()
        selected_level_name = degree_level_var.get()
        college_id = college_name_to_id.get(selected_college_name)

        degree_combo["values"] = []
        degree_var.set("")
        job_combo["values"] = []
        job_var.set("")
        job_desc_text.delete("1.0", "end")

        if college_id is None or not selected_dept_name or not selected_level_name:
            return

        try:
            departments = get_departments(college_id)
            department_id = None
            for row in departments:
                if row["name"] == selected_dept_name:
                    department_id = row["department_id"]
                    break
            if department_id is None:
                logger.warning(
                    "Department '%s' not found while resolving degree levels.",
                    selected_dept_name,
                )
                return

            levels = get_degree_levels(department_id)
            degree_level_id = None
            for row in levels:
                if row["name"] == selected_level_name:
                    degree_level_id = row["degree_level_id"]
                    break
            if degree_level_id is None:
                logger.warning(
                    "Degree level '%s' not found for department_id %s",
                    selected_level_name,
                    department_id,
                )
                return

            degrees = get_degrees(degree_level_id)
            names = [row["name"] for row in degrees]
            degree_combo["values"] = names
        except Exception as exc:
            logger.error(
                "Failed to refresh degrees for degree level '%s': %s",
                selected_level_name,
                exc,
            )

    def on_degree_selected(event=None):
        """Update jobs when a degree is selected."""
        selected_college_name = college_var.get()
        selected_dept_name = department_var.get()
        selected_level_name = degree_level_var.get()
        selected_degree_name = degree_var.get()
        college_id = college_name_to_id.get(selected_college_name)

        job_combo["values"] = []
        job_var.set("")
        job_desc_text.delete("1.0", "end")

        if (
            college_id is None
            or not selected_dept_name
            or not selected_level_name
            or not selected_degree_name
        ):
            return

        try:
            departments = get_departments(college_id)
            department_id = None
            for row in departments:
                if row["name"] == selected_dept_name:
                    department_id = row["department_id"]
                    break
            if department_id is None:
                logger.warning(
                    "Department '%s' not found while resolving degrees.",
                    selected_dept_name,
                )
                return

            levels = get_degree_levels(department_id)
            degree_level_id = None
            for row in levels:
                if row["name"] == selected_level_name:
                    degree_level_id = row["degree_level_id"]
                    break
            if degree_level_id is None:
                logger.warning(
                    "Degree level '%s' not found while resolving degrees.",
                    selected_level_name,
                )
                return

            degrees = get_degrees(degree_level_id)
            degree_id = None
            for row in degrees:
                if row["name"] == selected_degree_name:
                    degree_id = row["degree_id"]
                    break
            if degree_id is None:
                logger.warning(
                    "Degree '%s' not found for degree_level_id %s",
                    selected_degree_name,
                    degree_level_id,
                )
                return

            jobs = get_jobs_by_degree(degree_id)
            names = [job["name"] for job in jobs]
            job_combo["values"] = names
        except Exception as exc:
            logger.error(
                "Failed to refresh jobs for degree '%s': %s",
                selected_degree_name,
                exc,
            )

    def on_job_selected(event=None):
        """Update job description when a job is selected."""
        selected_job_name = job_var.get()
        selected_degree_name = degree_var.get()
        selected_level_name = degree_level_var.get()
        selected_dept_name = department_var.get()
        selected_college_name = college_var.get()

        job_desc_text.delete("1.0", "end")

        if (
            not selected_job_name
            or not selected_degree_name
            or not selected_level_name
            or not selected_dept_name
        ):
            return

        college_id = college_name_to_id.get(selected_college_name)
        if college_id is None:
            return

        try:
            departments = get_departments(college_id)
            department_id = None
            for row in departments:
                if row["name"] == selected_dept_name:
                    department_id = row["department_id"]
                    break
            if department_id is None:
                return

            levels = get_degree_levels(department_id)
            degree_level_id = None
            for row in levels:
                if row["name"] == selected_level_name:
                    degree_level_id = row["degree_level_id"]
                    break
            if degree_level_id is None:
                return

            degrees = get_degrees(degree_level_id)
            degree_id = None
            for row in degrees:
                if row["name"] == selected_degree_name:
                    degree_id = row["degree_id"]
                    break
            if degree_id is None:
                return

            jobs = get_jobs_by_degree(degree_id)
            for job in jobs:
                if job["name"] == selected_job_name:
                    job_desc_text.insert("1.0", job.get("description", ""))
                    break
        except Exception as exc:
            logger.error(
                "Failed to update job description for job '%s': %s",
                selected_job_name,
                exc,
            )

    college_combo.bind("<<ComboboxSelected>>", on_college_selected)
    department_combo.bind("<<ComboboxSelected>>", on_department_selected)
    degree_level_combo.bind("<<ComboboxSelected>>", on_degree_level_selected)
    degree_combo.bind("<<ComboboxSelected>>", on_degree_selected)
    job_combo.bind("<<ComboboxSelected>>", on_job_selected)

    # Start with empty, DB-driven values; handlers fill these in.
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

        # Persist ID-based preferences to User_Preferences
        try:
            college_id = None
            department_id = None
            degree_level_id = None
            degree_id = None
            job_id = None

            selected_college_name = college_var.get()
            if selected_college_name and selected_college_name in college_name_to_id:
                college_id = college_name_to_id[selected_college_name]

            if college_id is not None and department_var.get():
                departments = get_departments(college_id)
                for row in departments:
                    if row["name"] == department_var.get():
                        department_id = row["department_id"]
                        break

            if department_id is not None and degree_level_var.get():
                levels = get_degree_levels(department_id)
                for row in levels:
                    if row["name"] == degree_level_var.get():
                        degree_level_id = row["degree_level_id"]
                        break

            if degree_level_id is not None and degree_var.get():
                degrees = get_degrees(degree_level_id)
                for row in degrees:
                    if row["name"] == degree_var.get():
                        degree_id = row["degree_id"]
                        break

            if degree_id is not None and job_var.get():
                jobs = get_jobs_by_degree(degree_id)
                for job in jobs:
                    if job["name"] == job_var.get():
                        job_id = job["job_id"]
                        break

            db_pref_payload = {
                "college_id": college_id,
                "department_id": department_id,
                "degree_level_id": degree_level_id,
                "degree_id": degree_id,
                "job_id": job_id,
            }
            if current_user and "id" in current_user:
                ok = save_user_preferences(current_user["id"], db_pref_payload)
                if not ok:
                    logger.error(
                        "save_user_preferences returned False for user_id %s",
                        current_user["id"],
                    )
        except Exception as exc:
            logger.error("Failed to persist preferences to database: %s", exc)

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

    # header_label = tk.Label(
    #     frame, text="Course Recommendations", font=(TP_FONT_FAMILY, 14)
    # )
    # header_label.pack(pady=20)
    # added for dynamic text update
    header_text_var = tk.StringVar(value="Course Recommendations")
    header_label = tk.Label(frame, textvariable=header_text_var, font=("Helvetica", 14))
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

    # Store refs on the frame so generate_recommendations_ui can reuse them
    frame._rec_header_text_var = header_text_var
    frame._rec_header_default_text = "Course Recommendations"  
    frame._rec_generate_button = generate_button
    frame._rec_frame = rec_frame


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
    canvas = tk.Canvas(
        rec_frame,
        borderwidth=0,
        background=theme.CONTENT_BG,  # NEW: dark background for recs
        highlightthickness=0,
    )
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
            font=(TP_FONT_FAMILY, 12, "bold"),
            background="#ffffff",
        )
        course_label.pack(anchor="w", padx=5, pady=5)

        # Units
        # BUG units = rec.get("Units", "N/A")
        units = rec.get("Units", "3")  # FIXED: Default to 3 units if missing
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
            command=lambda c=rec: show_course_details(
                rec_container, c
            ),  # NEW: pass course data
        )
        details_btn.pack(anchor="e", padx=5, pady=5)


# # Function to generate and display recommendations (Need to add live AI functionality and database)
# def generate_recommendations_ui(frame):
#     """Generates and displays course recommednations (Placeholder need to add functionality with AI and database)"""
#     global current_user

#     clear_content(frame)
#     set_active_button("Recommendations")
#     header_label = tk.Label(
#         frame, text="Course Recommendations", font=(TP_FONT_FAMILY, 14)
#     )
#     header_label.pack(pady=20)

#     # Loading label
#     loading_label = tk.Label(
#         frame, text="Generating recommendations, please wait...", font=(TP_FONT_FAMILY, 12)
#     )
#     loading_label.pack(pady=10)
#     frame.update()

#     try:
#         required_fields = ["college", "department", "degree_level", "degree", "job"]
#         missing_fields = [
#             field
#             for field in required_fields
#             if field not in current_user or not current_user[field]
#         ]
#         if missing_fields:
#             messagebox.showwarning(
#                 "Incomplete Preferences",
#                 f"Please complete your preferences before generating recommendations. Missing: {', '.join(missing_fields)}",
#             )
#             logger.warning(
#                 f"Cannot generate recommendations, missing preferences: {missing_fields}"
#             )
#             show_preferences(frame)
#             return

#         # Parse electives from CSV
#         csv_path = os.path.join("database", "courses.csv")
#         if not os.path.exists(csv_path):
#             raise FileNotFoundError(f"Electives CSV file not found at {csv_path}")

#         with open(csv_path, "r", encoding="utf-8") as f:
#             csv_text = f.read()
#         degree_electives = _parse_degree_electives_csv(csv_text)

#         # Get recommendations from AI module
#         job_name = current_user["job"]
#         degree_name = current_user["degree"]
#         job_id = 1  # Placeholder job ID

#         response = get_recommendations_ai(
#             job_id=job_id,
#             job_name=job_name,
#             degree_name=degree_name,
#             degree_electives=degree_electives,
#         )
#         recommendations = parse_recommendations(response)
#         if not recommendations:
#             messagebox.showerror(
#                 "AI Error", "Failed to parse recommendations. Please try again."
#             )
#             logger.error("No recommednations parsed from AI response.")
#             return
#         rec_frame = frame.winfo_children()[-1]  # Get the last child, which is rec_frame
#         clear_content(rec_frame)
#         display_recommendations_ui(rec_frame, recommendations)

#         # Old Logic
#         """
#         # Parse JSON response
#         rec_data = json.loads(response)
#         loading_label.destroy()  # Remove loading label

#         # Display recommendations
#         results_frame = ttk.Frame(frame)
#         results_frame.pack(pady=10, padx=20, fill="both", expand=True)

#         canvas = tk.Canvas(results_frame)
#         scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
#         scrollable_frame = ttk.Frame(canvas)

#         scrollable_frame.bind(
#             "<Configure>",
#             lambda e: canvas.configure(
#                 scrollregion=canvas.bbox("all")
#             ))
#         canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
#         canvas.configure(yscrollcommand=scrollbar.set)
#         canvas.pack(side="left", fill="both", expand=True)
#         scrollbar.pack(side="right", fill="y")

#         # Show each recommended course
#         if isinstance(rec_data, list) and rec_data:
#             for course in rec_data:
#                 title = course.get("Course Name", "N/A")
#                 desc = course.get("Description", "No description available.")
#                 units = course.get("Units", "N/A")
#                 prereqs = ", ".join([course.get(f"Prereq{i}", "") for i in range(1, 4) if course.get(f"Prereq{i}")])
#                 card = ttk.LabelFrame(scrollable_frame, text=title)
#                 card.pack(fill="x", pady=5, padx=5)

#                 info = f"Units: {units}\nPrerequisites: {prereqs}\n\n{desc}"
#                 tk.Label(card, text=info, justify = "left", wraplength=800, font=(TP_FONT_FAMILY, 10, "bold")).pack(anchor="w", padx=10, pady=5)

#         else:
#            tk.Label(scrollable_frame, text="No recommendations found.", font=(TP_FONT_FAMILY, 12)).pack(pady=20)
#            logger.info("No recommendations returned from AI module.")
#  """
#         logger.info("Course recommendations generated and displayed successfully.")
#     except Exception as e:
#         messagebox.showerror("Error", f"An error occurred: {e}")
#         logger.error(f"Error checking user preferences: {e}")
#         return


def get_current_user_preferences():
    """Fetches the current user's preferences from the database."""
    if not current_user:
        logger.error("No user is currently logged in.")
        messagebox.showerror("Error", "No user is currently logged in.")
        return None

    user_id = current_user.get("id")
    preferences = db_operations.get_user_preferences(user_id)
    if not preferences:
        logger.warning(f"No preferences found for user_id {user_id}.")
        messagebox.showwarning(
            "No Preferences", "You have not set any preferences yet."
        )
    return preferences

def generate_recommendations_ui(frame):
    """Generates and displays AI-driven course recommendations."""
    logger.info("Generating course recommendations.")

    header_text_var = getattr(frame, "_rec_header_text_var", None)
    default_header_text = getattr(frame, "_rec_header_default_text", "Course Recommendations")
    generate_button = getattr(frame, "_rec_generate_button", None)  # Added Code
    toplevel = frame.winfo_toplevel()

    # Disable the Generate button immediately on entry  # Added Code
    if generate_button is not None:  # Added Code
        generate_button.config(state="disabled")  # Added Code
        toplevel.update_idletasks()  # Added Code

    # Update header text while generating
    if header_text_var is not None:
        header_text_var.set("Generating recommendations, please wait...")
        toplevel.update_idletasks()

    try:
        rec_frame = getattr(frame, "_rec_frame", None)  # Added Code
        if rec_frame is None:  # Added Code
            rec_frame = frame.winfo_children()[-1]  # fallback  # Added Code

        clear_content(rec_frame)

        # Fetch user preferences
        user_prefs = get_current_user_preferences()
        if not user_prefs:
            logger.error("Cannot generate recommendations without user preferences.")
            messagebox.showerror(
                "Error", "Cannot generate recommendations without user preferences."
            )
            return

        # Extract job_id, degree_id from user_prefs
        job_id = user_prefs.get("job_id")
        degree_id = user_prefs.get("degree_id")

        if not job_id:
            logger.error("User preferences do not include a job_id.")
            messagebox.showerror("Error", "Please set your job preference in Preferences.")
            return

        if not degree_id:
            logger.error("User preferences do not include a degree_id.")
            messagebox.showerror("Error", "Please set your degree preference in Preferences.")
            return

        # Retrieve job_name from job_id
        try:
            job = db_operations.get_job_by_id(job_id)
            if job:
                job_name = job["name"]
            else:
                logger.error(f"No job found with job_id {job_id}.")
                messagebox.showerror("Error", "Invalid job preference.")
                return
        except Exception as e:
            logger.error(f"Error retrieving job name for job_id {job_id}: {e}")
            messagebox.showerror("Error", "Failed to retrieve job information.")
            return

        # Retrieve degree_name from degree_id
        try:
            degree = db_operations.get_degree_by_id(degree_id)
            if degree:
                degree_name = degree["name"]
            else:
                logger.error(f"No degree found with degree_id {degree_id}.")
                messagebox.showerror("Error", "Invalid degree preference.")
                return
        except Exception as e:
            logger.error(f"Error retrieving degree name for degree_id {degree_id}: {e}")
            messagebox.showerror("Error", "Failed to retrieve degree information.")
            return

        # Fetch degree electives
        try:
            degree_electives = db_operations.get_degree_electives(degree_id)
            logger.debug(f"Fetched {len(degree_electives)} degree electives.")
        except Exception as e:
            logger.error(f"Error fetching degree electives: {e}")
            messagebox.showerror("Error", "Failed to fetch degree electives.")
            return

        # Invoke AI to get recommendations
        try:
            recommendations_raw = get_recommendations_ai(
                job_id, job_name, degree_name, degree_electives
            )
            logger.debug("AI Recommendations Raw Response:")
            logger.debug(recommendations_raw)
        except Exception as e:
            messagebox.showerror(
                "AI Error",
                "Failed to generate recommendations. Please try again later.",
            )
            logger.error(f"Failed to generate recommendations: {e}")
            return

        # Parse the AI response
        recommendations = parse_recommendations(recommendations_raw)
        if not recommendations:
            messagebox.showerror(
                "AI Error", "Failed to parse recommendations. Please try again."
            )
            logger.error("No recommendations parsed from AI response.")
            return

        # Display the recommendations
        display_recommendations_ui(rec_frame, recommendations)

        # Save recommendations to the database
        try:
            user_id = current_user["id"]
            db_operations.clear_recommendations(user_id, job_id)
            save_recommendations_to_db(user_id, job_id, recommendations)
            logger.info("Recommendations generated and saved successfully.")
        except KeyError as ke:
            logger.error(f"Error saving recommendations to database: {ke}")
            messagebox.showerror("Error", f"Error saving recommendations to database: {ke}")
        except Exception as e:
            logger.error(f"Error saving recommendations to database: {e}")
            messagebox.showerror("Error", "Failed to save recommendations to database.")

    finally:
        # Restore header text
        if header_text_var is not None:
            header_text_var.set(default_header_text)

        # Re-enable the Generate button on exit (even on errors/returns)  # Added Code
        if generate_button is not None:  # Added Code
            generate_button.config(state="normal")  # Added Code

        toplevel.update_idletasks()





# def save_recommendations_to_db(recommendations):
#     """Saves Recommendations to the database (Placeholder function)"""
#     saved_count = 0
def save_recommendations_to_db(user_id, job_id, recommendations):
    """
    Saves the list of course recommendations to the Recommendations table.

    :param user_id: int, The ID of the user.
    :param job_id: int, The ID of the job associated with the recommendations.
    :param recommendations: list of dicts, The course recommendations.
    """

    """
    Process:
        Iterate through each recommendation.
        Extract course_code, rating, explanation, and rank.
        Fetch course_id using db_operations.get_course_by_code(course_code).
        Save the recommendation using db_operations.save_recommendation.
    """

    saved_count = 0  # Counter for successfully saved recommendations

    for rec in recommendations:
        # Access fields using indexing instead of .get()
        course_code = rec["Course Code"] if "Course Code" in rec else None
        rating = rec["Rating"] if "Rating" in rec else None
        explanation = (
            rec["Explanation"] if "Explanation" in rec else "No explanation provided."
        )
        rank = rec["Number"] if "Number" in rec else 0  # Assign default rank if missing

        # Validate required fields
        if not course_code:
            logger.warning("Recommendation missing 'Course Code'. Skipping.")
            continue
        if rating is None:
            logger.warning(
                f"Recommendation for {course_code} missing 'Rating'. Skipping."
            )
            continue

        # Fetch course_id from course_code
        course = db_operations.get_course_by_code(course_code)
        if not course:
            logger.warning(f"Course with code {course_code} not found in database.")
            continue  # Skip if course not found

        # Access course_id using indexing

        # Access course_id more reliably
        course_id = course["course_id"]
        if course_id is None:
            logger.warning(f"Course ID for course code {course_code} is missing.")
            continue  # Skip if course_id is missing

        # Handle rank if 'Number' is missing or invalid
        if not isinstance(rank, int):
            logger.warning(
                f"Recommendation for course {course_code} has invalid 'Number': {rank}. Assigning default rank."
            )
            rank = 0  # Assign default rank

        # Save the recommendation
        try:
            success = db_operations.save_recommendation(
                user_id=user_id,
                job_id=job_id,
                course_id=course_id,
                rating=rating,
                explanation=explanation,
                rank=rank,
            )
            if success:
                saved_count += 1
                logger.info(
                    f"Recommendation for course {course_code} saved successfully."
                )
            else:
                logger.error(f"Failed to save recommendation for course {course_code}.")
        except Exception as e:
            logger.error(f"Error saving recommendation for course {course_code}: {e}")

    logger.info(
        f"Total Recommendations Saved: {saved_count} out of {len(recommendations)}"
    )


# Placeholder for course details page
def show_course_details(frame, course=None):  # NEW: accept optional course dict
    """Display for course details"""
    clear_content(frame)
    text = "Course Details Page"
    if course is not None:
        text = f"{course.get('Course Name', 'Course Details')} ({course.get('Course Code', 'N/A')})"
    tk.Label(frame, text=text, font=(TP_FONT_FAMILY, 14)).pack(pady=20)


# Placeholder for profile page
def show_profile(frame):
    """Display for User Profile and Account Settings"""
    logger.info("Displaying Profile Page")
    set_active_button("Profile")
    clear_content(frame)
    global current_user

    profile_header = tk.Label(frame, text="User Profile", font=(TP_FONT_FAMILY, 14))
    profile_header.pack(pady=20)

    full_name = f"{current_user.get('first_name', 'N/A')} {current_user.get('last_name', '')}".strip()
    profile_name_label = tk.Label(
        frame, text=f"Name: {full_name}", font=(TP_FONT_FAMILY, 12)
    )
    profile_name_label.pack(pady=5)

    profile_email_label = tk.Label(
        frame,
        text=f"Email: {current_user.get('email', 'N/A')}",
        font=(TP_FONT_FAMILY, 12),
    )
    profile_email_label.pack(pady=5)

    # Section heading (NEW)
    settings_title = tk.Label(
        frame,
        text="Account Settings",
        font=SUBHEADER_FONT,
        bg=TP_BG,
        fg=TP_TEXT_PRIMARY,
        bd=0,
        highlightthickness=0,
        relief="flat",
        anchor="w",
    )
    settings_title.pack(pady=(20, 5), fill="x", padx=20)

    settings_frame = ttk.Frame(frame)  # (CHANGED from LabelFrame)
    settings_frame.pack(pady=(0, 20), fill="x", padx=20)
    def change_email():
        """Changes Email"""
        logger.info("User initiated email change.")
        email_window = tk.Toplevel(frame)
        email_window.title("Change Email")

        ttk.Label(email_window, text="New Email:").pack(pady=10, padx=10, anchor="w")
        new_email_entry = ttk.Entry(email_window, width=30)
        new_email_entry.pack(pady=5, padx=10, anchor="w")

        ttk.Label(email_window, text="Confirm New Email:").pack(pady=10, padx=10, anchor="w")
        confirm_email_entry = ttk.Entry(email_window, width=30)
        confirm_email_entry.pack(pady=5, padx=10, anchor="w")

        def perform_email_change():
            new_email = new_email_entry.get().strip().lower()
            confirm_email = confirm_email_entry.get().strip().lower()

            if (not new_email) or ("@" not in new_email):
                messagebox.showerror(
                    "Error", "Please enter a valid email address.", parent=email_window
                )
                return
            if new_email != confirm_email:
                messagebox.showerror(
                    "Error", "Email addresses do not match.", parent=email_window
                )
                return
            # open db connection
            conn = get_db_connection()
            if not conn:
                messagebox.showerror(
                    "Error",
                    "Database connection error. Please try again later.",
                    parent=email_window,
                )
                return
            try: 
                cursor = conn.cursor()
                # check if email already exists
                cursor.execute("SELECT id FROM users WHERE email = ?", (new_email,))
                if cursor.fetchone():
                    messagebox.showerror(
                        "Error", "Email is already in use.", parent=email_window
                   )
                    return
                # update email in DB
                cursor.execute(
                    "UPDATE users SET email = ? WHERE id = ?",
                    (new_email, current_user["id"]),
                )
                conn.commit()

                # update in-memory user
                current_user["email"] = new_email
                status_var.set(f"Logged in as: {current_user['first_name']} {current_user['last_name']}")
                messagebox.showinfo("Success", "Email updated successfully!", parent=email_window)

                # Refresh profile page
                show_profile(frame)
                email_window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror(
                    "Error", "Email is already in use.", parent=email_window
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"An error occurred while updating email: {e}",
                    parent=email_window,
                )
                logger.error(f"Error updating email for user '{current_user['email']}': {e}")
            finally:
                conn.close()
        save_email_button = ttk.Button(
            email_window, text="Save Email", command=perform_email_change
        )
        save_email_button.pack(pady=15)
        cancel_button = ttk.Button(
            email_window, text="Cancel", command=email_window.destroy
        )
        cancel_button.pack(pady=(0,10))

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

    change_password_button = tk.Button(  # (CHANGED to tk.Button for custom colors)
        settings_frame,
        text="Change Password",
        command=change_password,
        bg=TP_ACCENT,
        fg=TP_TEXT_PRIMARY,
        activebackground=TP_ACCENT,
        activeforeground=TP_TEXT_PRIMARY,
        bd=0,
        font=BASE_FONT,
    )
    change_password_button.pack(pady=10, padx=10, fill="x")

    change_email_button = tk.Button(
        settings_frame,
        text="Change Email",
        command=change_email,
        bg=TP_ACCENT,
        fg=TP_TEXT_PRIMARY,
        activebackground=TP_ACCENT,
        activeforeground=TP_TEXT_PRIMARY,
        bd=0,
        font=BASE_FONT,
    )
    change_email_button.pack(pady=10, padx=10, fill="x")
# Placeholder for Help Page
def show_help(frame):
    """Display the Help Page"""
    logger.info("Displaying Help Page")
    clear_content(frame)
    set_active_button("Help")
    theme.style_main_frame(frame)  # NEW: TitanPark background for Help

    header_label = ttk.Label(frame, text="Help & Support", font=(TP_FONT_FAMILY, 20))
    header_label.configure(background=theme.CONTENT_BG, foreground=theme.TEXT_PRIMARY)
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
        font=(TP_FONT_FAMILY, 14),
        wraplength=800,
        justify="left",
    )
    help_label.configure(background=theme.CARD_BG, foreground=theme.TEXT_MUTED)
    help_label.pack(pady=10)

    search_label = ttk.Label(
        help_frame, text="Search Help Topics:", font=(TP_FONT_FAMILY, 12)
    )
    search_label.pack(pady=5, anchor="w")
    search_entry = ttk.Entry(help_frame, width=50)
    search_entry.pack(pady=5, anchor="w")

    def search_help():
        query = search_entry.get()
        messagebox.showinfo("Coming soon", "coming soon")

    search_button = ttk.Button(help_frame, text="Search", command=search_help)
    search_button.pack(pady=5, anchor="w")

    # Push the About button to the bottom-right
    help_frame.pack_propagate(False)
    spacer = ttk.Frame(help_frame)
    spacer.pack(fill="both", expand=True)
    about_button = ttk.Button(
        help_frame,
        text="About",
        command=lambda: show_about_dialog(frame),
    )
    about_button.pack(pady=10, anchor="e")


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
