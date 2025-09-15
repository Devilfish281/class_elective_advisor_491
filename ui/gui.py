import logging
import threading
import time
import tkinter as tk
from tkinter import ttk, PhotoImage
from typing import Optional

logger = logging.getLogger(__name__)  # Reuse the global logger

# Dictionary to store navigation buttons
nav_buttons = {}
# Dictionary to store loaded icons
nav_icons = {}

def main_int_ui() -> None:
    """Initializes and runs the main interface of the Smart Elective Advisor."""

    logger.info("Initializing the Smart Elective Advisor GUI.")

    # Minimal Tkinter window
    root = tk.Tk()
    root.title("Smart Elective Advisor")
    root.geometry("1200x800")

    # Grid Layout
    root.columnconfigure(0, weight=1) # Navigation Menu
    root.columnconfigure(1, weight=4) # Content Display
    root.rowconfigure(0, weight=1)
    
    # Create Navigation Menu Frame
    nav_frame = ttk.Frame(root, width=200, relief="raised")
    nav_frame.grid(row=0, column=0, sticky="ns")
    nav_frame.grid_propagate(False)
    nav_frame.columnconfigure(0, weight=1)

    # Content Area
    content_frame = tk.Frame(root, bg = "white")
    content_frame.grid(row=0, column=1, sticky="nsew")

    # Styles for sidebar buttons 
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", padding=5, anchor='w', font=("Helvetica, 12"))
    style.map(
        "TButton",
        background=[("pressed", "#d0e0ff"), ("active","#f0f0f0")]
    )
    
    # Highlights active buttons
    def set_active_button(label):
        for name, btn in nav_buttons.items():
            if name == label:
                btn.state(["pressed"])
            else:
                btn.state(["!pressed"])


    # Menu Items
    menu_items = [
        ("Home", "icons/home.png", show_home),
        ("Login", "icons/login.png", show_login),
        ("Logout", "icons/logout.png", show_logout),
        ("Registration", "icons/register.png", show_registration),
        ("Preferences", "icons/preferences.png", show_preferences),
        ("Recommendations", "icons/recommendations.png", show_recommendations),
        ("Profile", "icons/profile.png", show_profile),
        ("Help", "icons/help.png", show_help),
    ]

    # Creates Navigation buttons with icons
    for i, (label, icon_path, command) in enumerate(menu_items):
        try:
            icon = PhotoImage(file=icon_path)
            nav_icons[label] = icon
            btn = ttk.Button(
                nav_frame, text=label, image=icon, compound = "left",
                command=lambda c=command: c(content_frame)
            )
        except Exception as e:
            logger.warning(f"Could not load icon {icon_path}: {e}")
            btn = ttk.Button(
                nav_frame, text=label,
                command=lambda c=command: c(content_frame)
            )
        
        btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")
        nav_buttons[label]=btn


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

def show_home(frame):
    """Displays the Home Dashboard"""
    clear_content(frame)
    label = tk.Label(frame, text="Welcome to Smart Elective Advisor", font = ("Helvetica", 16))
    label.pack(padx=20, pady=20)
    info_text = (
        "The Smart Elective Advisor helps CS students select the best elective courses based on their "
        "interests, career aspirations, and academic performance. Navigate through the menu to get started."
    )
    info = tk.Label(frame, text = info_text, wraplength=500, justify="center")
    info.pack(pady=10) 

# Login Page
def show_login(frame):
    """Displays the Login Page."""
    clear_content(frame)
    header_label = tk.Label(frame, text = "Login Page", font = ("Helvetica", 14))
    header_label.pack(pady=20)

    # Email
    email_label = tk.Label(frame, text="Email:")
    email_label.pack(pady=(10, 5))
    email_entry = tk.Entry(frame, width=30)
    email_entry.pack(pady=(0, 10))

    # Password 
    password_label = tk.Label(frame, text="Password:")
    password_label.pack(pady=(10,5))
    password_entry = tk.Entry(frame, width=30, show="*")
    password_entry.pack(pady=(0,10))


    # Login Button (Need to add function for logging in)
    login_button = tk.Button(frame, text="Login", width=15)
    login_button.pack(pady=(20, 10))

    # Forgot password and Register links
    tk.Label(frame, text="Forgot password?", fg="blue", cursor="hand2").pack(pady=(5, 2))
    tk.Label(frame, text="Don't have an account? Register", fg="blue", cursor="hand2").pack(pady=(2, 10))


#Placeholder for Logout
def show_logout(frame):
    """Handles user logging out."""
    clear_content(frame)
    tk.Label(frame, text = "Logout Page", font = ("Helvetica", 14)).pack(pady=20)

# Placeholder for registration page
def show_registration(frame):
    """Display for Registration Page"""
    clear_content(frame)
    tk.Label(frame, text = "Registration Page", font = ("Helvetica", 14)).pack(pady=20)

# Placeholder for preferences
def show_preferences(frame):
    """Display for Preferences"""
    clear_content(frame)
    tk.Label(frame, text = "Preferences Page", font = ("Helvetica", 14)).pack(pady=20)

# Placeholder for recommendations page
def show_recommendations(frame):
    """Display for Recommendations Page"""
    clear_content(frame)
    tk.Label(frame, text = "Recommendations Page", font = ("Helvetica", 14)).pack(pady=20)

# Placeholder for course details page
def show_course_details(frame):
    """Display for course details"""
    clear_content(frame)
    tk.Label(frame, text = "Course Details Page", font = ("Helvetica", 14)).pack(pady=20)

# Placeholder for profile page
def show_profile(frame):
    """Display for Profile Page"""
    clear_content(frame)
    tk.Label(frame, text = "Profile Page", font = ("Helvetica", 14)).pack(pady=20)

# Placeholder for Help Page
def show_help(frame):
    """Display the Help Page"""
    clear_content(frame)
    tk.Label(frame, text = "Help Page", font = ("Helvetica", 14)).pack(pady=20)



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