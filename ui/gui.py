import logging
import threading
import time
import tkinter as tk
from tkinter import ttk, PhotoImage, messagebox
from typing import Optional

logger = logging.getLogger(__name__)  # Reuse the global logger

# Global variables for login status and current users
login_status = False
current_user = None

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
    root.columnconfigure(0, weight=0) # Navigation Menu
    root.columnconfigure(1, weight=1) # Content Display
    root.rowconfigure(0, weight=1)
    
    # Create Navigation Menu Frame
    nav_frame = tk.Frame(root, width=220, relief="raised", bg="#F7F7F7")
    nav_frame.grid(row=0, column=0, sticky="ns")
    nav_frame.grid_propagate(False)
    nav_frame.columnconfigure(0, weight=1)

    # Content Area
    content_frame = tk.Frame(root, bg = "white", relief="groove", bd=2)
    content_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

    # Styles for sidebar buttons 
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", padding=5, anchor='w', font=("Helvetica", 12), background="white")
    style.map(
        "TButton",
        background=[("pressed", "#FF7900"), ("active","#FF7900")]
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
        nav_buttons["Login"].grid_remove() # removes login button 
        nav_buttons["Registration"].grid_remove() # removes registration button

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
users = {
    "student@test.com": {   
    "password": "password123",
    "name": "Test Student"
    }
}

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

    def handle_login():
        """Handles login(need to connect to database)"""
        global login_status, current_user
        email = email_entry.get()
        password = password_entry.get()
        logger.debug(f"Attempting login with email: {email}")
        # Check against test user data
        if email in users and password == users[email]["password"]:
            login_status = True
            current_user = {"email": email, "name": users[email]["name"]}
            messagebox.showinfo(
                "Login Successful", f"Welcome back, {users[email]['name']}!"
                )
            
            logger.info(f"User '{email}' logged in successfully.")
            show_preferences(frame) # Redirect to preferences page after login
            update_nav_buttons() # Refreshes button states
        else:
            messagebox.showerror("Login Failed", "Invalid email or password. Please try again.")
            logger.warning(f"Login failed for email: {email}")

    # Login Button (Need to add function for logging in)
    login_button = tk.Button(frame, text="Login", width=15, command=handle_login)
    login_button.pack(pady=(20, 10))

    # Forgot password link
    forgot_password_label = tk.Label(frame, text="Forgot password?", fg="blue", cursor="hand2")
    forgot_password_label.pack(pady=(5, 2))
    
    # Registration link 
    reg_label = tk.Label(frame, text="Don't have an account? Register", fg="blue", cursor="hand2")
    reg_label.pack(pady=(2,10))
    reg_label.bind("<Button-1>", lambda e: show_registration(frame))

#Placeholder for Logout
def show_logout(frame):
    """Handles user logging out."""
    global login_status, current_user
    clear_content(frame)
    logger.info("User initaited logout.")

    login_status = False # reset login status
    current_user = None # clear current user

    messagebox.showinfo("Logout Successful", "You have been logged out.")
    logger.info("User logged out successfully.")
    show_home(frame) # Redirect to home page after logout
    update_nav_buttons() # Refresh button states

# Registration page
def show_registration(frame):
    """Display for Registration Page"""
    global login_status, current_user
    logger.info("Displaying User Registration Form")
    clear_content(frame)
    header_label = tk.Label(frame, text = "User Registration", font = ("Helvetica", 14))
    header_label.pack(pady=20)

    # Registration Form Frame
    reg_frame = ttk.Frame(frame)
    reg_frame.pack(pady=10)

    # Full name
    name_label = ttk.Label(reg_frame, text="Full Name:")
    name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    name_entry = ttk.Entry(reg_frame, width=30)
    name_entry.grid(row=0, column=1, padx=5, pady=5)

    # Email
    email_label = ttk.Label(reg_frame, text="Email:")
    email_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    email_entry = ttk.Entry(reg_frame, width=30)
    email_entry.grid(row=1, column=1, padx=5, pady=5)

    # Password
    password_label = ttk.Label(reg_frame, text="Password:")
    password_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
    password_entry = ttk.Entry(reg_frame, width=30, show="*")
    password_entry.grid(row=2, column=1, padx=5, pady=5)

    # Confirm Password
    confirm_label = ttk.Label(reg_frame, text="Confirm Password:")
    confirm_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
    confirm_entry = ttk.Entry(reg_frame, width=30, show="*")
    confirm_entry.grid(row=3, column=1, padx=5, pady=5)

    def handle_registration():
        """Handles User Registration (need to add input validations, character length for password, special characters, and register new users in database)"""
        name = name_entry.get().strip()
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        confirm_password = confirm_entry.get().strip()

        if not name or not email or not password or not confirm_password:
            messagebox.showerror("Error", "All fields are required.")
            return
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        if email in users:
            messagebox.showerror("Error", "Email already registered. Please login.")
            return
        if not name:
            messagebox.showerror("Input Error", "Please enter your full name.")
            logger.warning("Registration failed: Full name not provided.")
            return
        if not email or "@" not in email:
            messagebox.showerror("Input Error", "Please enter a valid email address.")
            logger.warning("Registration failed: Invalid email format.")
            return
        
        # Special characters
        password_special_chars = r"!@#$%^&*()-_=+[{]}\|;:'\",<.>/?'~"
        if (len(password) < 8 or not any(char.isdigit() for char in password)
                or not any(char in password_special_chars for char in password)):
            messagebox.showerror(
                "Input Error", "Password must be at least 8 characters long and include numbers and special characters."
            )
            logger.warning("Registration failed: Weak Password.")
            return
        
        # Save new user
        users[email] = {"name": name, "password":password}
        messagebox.showinfo("Success", "Registration successful! Please login.")
        logger.info(f"New user registered: {email}")

        # Redirect to login page
        show_login(frame)

     # Registration Button
    reg_button = tk.Button(frame, text="Register", width=20, command=handle_registration)
    reg_button.pack(pady=20)


# Placeholder for preferences
def show_preferences(frame):
     """Display for Preferences"""
     logger.info("Displaying the Preferences Form.")
     clear_content(frame)
     
     header_label = tk.Label(frame, text="Preferences Page", font=("Helvetica", 14, "bold"))
     header_label.pack(pady=20)

     pref_frame = ttk.Frame(frame)
     pref_frame.pack(pady=10)


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
    """Display for User Profile and Account Settings"""
    logger.info("Displaying Profile Page")
    clear_content(frame)
    global current_user

    profile_header = tk.Label(frame, text="User Profile", font=("Helvetica", 14))
    profile_header.pack(pady=20)

    profile_name_label = tk.Label(frame, text=f"Name: {current_user.get('name', 'N/A')}", font=("Helvetica", 12))
    profile_name_label.pack(pady=5)

    profile_email_label = tk.Label(frame, text=f"Email: {current_user.get('email', 'N/A')}", font=("Helvetica", 12))
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

            if current_password != users[current_user["email"]]["password"]:
                messagebox.showerror("Error", "Current password is incorrect.", parent=password_window)
                return
            if new_password != confirm_password:
                messagebox.showerror("Error", "New passwords do not match.", parent=password_window)
                return
            if len(new_password) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters long.", parent=password_window)
                return

            users[current_user["email"]]["password"] = new_password
            messagebox.showinfo("Success", "Password changed successfully!", parent=password_window)
            logger.info(f"User '{current_user['email']}' changed password.")
            password_window.destroy()

        save_password_button = ttk.Button(password_window, text="Save Password", command=perform_password_change)
        save_password_button.pack(pady=20)

    change_password_button = ttk.Button(settings_frame, text="Change Password", command=change_password)
    change_password_button.pack(pady=10, padx=10, fill="x")

# Placeholder for Help Page
def show_help(frame):
   """Display the Help Page""" 
   clear_content(frame)
   
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
   help_label = ttk.Label(help_frame, text=help_text, font=("Helvetica", 14), wraplength=800, justify="left")
   help_label.pack(pady=10)

   search_label = ttk.Label(help_frame, text="Search Help Topics:", font=("Helvetica", 12))
   search_label.pack(pady=5, anchor="w")
   search_entry = ttk.Entry(help_frame, width=50)
   search_entry.pack(pady=5, anchor="w")
   def search_help():
        query = search_entry.get()
        messagebox.showinfo("Coming soon", "coming soon")
    
   search_button = ttk.Button(help_frame, text="Search", command=search_help)
   search_button.pack(pady=5, anchor="w")

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