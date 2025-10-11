#ui/gui.py
import logging
import os
import csv
import json
import threading
import time
import tkinter as tk
import bcrypt # For password hashing (if needed in future)
from tkinter import ttk, PhotoImage, messagebox
from typing import Optional
import sqlite3
from database import db_add # For database interactions
from ai_integration.ai_module import get_recommendations_ai, _parse_degree_electives_csv # AI integration


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
    style.configure("Active.TButton", padding=5, anchor='w', font=("Helvetica", 12, "bold"), background="#FF7900", foreground="white")
    
    # Status bar at the bottom
    global status_var
    status_var = tk.StringVar()
    status_var.set("Not logged in")

    status_bar = tk.Label(root, textvariable=status_var, bd=1, relief="sunken", anchor="w")
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
    set_active_button("Login")
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
    # Frame to hold password entry and eye icon
    pw_frame = ttk.Frame(frame)
    pw_frame.pack(pady=(0,10))

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
        email = email_entry.get()
        password = password_entry.get()
        logger.debug(f"Attempting login with email: {email}")
       # user = users.get(email)
        conn = get_db_connection()
    # Check if connection was successful
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to the database. Please try again later.")
            logger.error("Login failed: Database connection error.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user[3].encode("utf-8")):
            login_status = True
            current_user = {
                "id": user[0],
                "email": email,
                "first_name": user[1],
                "last_name": user[2]
        }
            display_name = f"{user[1]} {user[2]}"
            status_var.set(f"Logged in as: {display_name}")
            messagebox.showinfo(
                "Login Successful", f"Welcome back, {display_name}!"
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
    set_active_button("Logout")
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
    set_active_button("Registration")
    global login_status, current_user
    logger.info("Displaying User Registration Form")
    clear_content(frame)
    header_label = tk.Label(frame, text = "User Registration", font = ("Helvetica", 14))
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
        """Handles User Registration """
        first_name = first_name_entry.get().strip()
        last_name = last_name_entry.get().strip()
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        confirm_password = confirm_entry.get().strip()

        if not first_name or not last_name or not email or not password or not confirm_password:
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
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()
        conn.close()

        if existing_user:
            messagebox.showerror("Error", "Email already registered. Please login.")
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
        
        # Hash the password before storing 
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            user_id = db_add.add_user(first_name, last_name, email, None, None, password_hash)
            logger.info(f"New user registered with ID: {email}")
            messagebox.showinfo("Success", "Registration successful! Please login.")
            logger.info(f"User '{email}' registered successfully.")
            show_login(frame)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Email already registered. Please login.")
            logger.warning(f"Registration failed: Email '{email}' already exists in database.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during registration: {e}")
            logger.error(f"Registration failed due to error: {e}")
            return
        
     # Registration Button
    reg_button = tk.Button(frame, text="Register", width=20, command=handle_registration)
    reg_button.pack(pady=20)


# Preferences Page (need to add functionality to load preferences from database)
def show_preferences(frame):
     """Display for Preferences"""
     # Guard to prevent unauthorized access
     if not login_status:
            messagebox.showwarning("Access Denied", "Please login to set preferences.")
            logger.warning("Unauthorized access attempt to Preferences Form.")
            return
     
     set_active_button("Preferences")
     logger.info("Displaying the Preferences Form.")
     clear_content(frame)
     
     # Header for preferences page
     header_label = tk.Label(frame, text="Preferences Page", font=("Helvetica", 14, "bold"))
     header_label.pack(pady=20)

    # Preferences Form Frame
     pref_frame = ttk.Frame(frame)
     pref_frame.pack(pady=10)

     # Exisiting Preferences (Placeholder will add functionality to fetch from database)
     exisiting_prefs = ["AI", "Machine Learning", "Data Science"]

     # College Selection (Placeholder will add functionality to fetch from database)
     college_label = ttk.Label(pref_frame, text="College of:")
     college_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
     college_var = tk.StringVar()
     college_combo = ttk.Combobox(
         pref_frame, textvariable=college_var, state="readonly", width=45
     )
     college_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

     # Department Selection (Placeholder will add functionality to fetch from database)
     department_label = ttk.Label(pref_frame, text="Department:")
     department_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
     department_var = tk.StringVar()
     department_combo = ttk.Combobox(
        pref_frame, textvariable=department_var, state="readonly", width=45
     )
     department_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

     # Degree Level Selection
     degree_level_label = ttk.Label(pref_frame, text="Degree Level:")
     degree_level_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
     degree_level_var = tk.StringVar()
     degree_level_combo = ttk.Combobox(
        pref_frame, textvariable=degree_level_var, state="readonly", width=45
     )
     degree_level_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

     # Degree Selection
     degree_label = ttk.Label(pref_frame, text="Degree:")
     degree_label.grid(row=3, column=0, padx=5, pady=5, sticky="e")
     degree_var = tk.StringVar()
     degree_combo = ttk.Combobox(
        pref_frame, textvariable=degree_var, state="readonly", width=45
     )
     degree_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

     # Job Selection
     job_label = ttk.Label(pref_frame, text="Preferred Job:")
     job_label.grid(row=4, column=0, padx=5, pady=5, sticky="e")
     job_var = tk.StringVar()
     job_combo = ttk.Combobox(
        pref_frame, textvariable=job_var, state="readonly", width=45
     )
     job_combo.grid(row=4, column=1, padx=5, pady=5, sticky="w")

     # Job Description
     job_desc_label = ttk.Label(frame, text="Job Description:")
     job_desc_label.pack(pady=(10, 0), anchor="w", padx=20)
     job_desc_text = tk.Text(frame, height=5, wrap="word", width=100)
     job_desc_text.pack(pady=5, padx=20, fill="x")

     # Dropdown data (Placeholder will add functionality to fetch from database)
     college_combo['values'] = ["College of Engineering", "College of Arts and Sciences", "College of Business"]
     degree_level_combo['values'] = ["Undergraduate", "Graduate"]
     degree_combo['values'] = ["B.S. Computer Science", "M.S. Software Engineering"]
     department_combo['values'] = ["Computer Science", "Information Technology", "Software Engineering"]
     job_combo['values'] = ["Software Engineer", "Data Scientist", "AI Specialist", "Web Developer"]

     def save_preferences():
         """Saves user preferences (Placeholder will add functionality to save to database)"""
         prefs = {
                "college": college_var.get(),
                "department": department_var.get(),
                "degree_level": degree_level_var.get(),
                "degree": degree_var.get(),
                "job": job_var.get(),
                "job_description": job_desc_text.get("1.0", "end").strip(),
         }
         current_user.update(prefs)  # Update current_user with preferences
         logger.info(f"User preferences saved: {prefs}")
         messagebox.showinfo("Preferences Saved", "Your preferences have been saved.")

     # Save Preferences Button
     save_button = tk.Button(frame, text="Save Preferences", width=20, command=save_preferences) 
     save_button.pack(pady=20)

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
    header_label = tk.Label(frame, text = "Course Recommendations", font = ("Helvetica", 14))
    header_label.pack(pady=20)

    # Generate Recommendations Button (need to add function to generate recommendations)
    generate_button = tk.Button(frame, text="Generate Recommendations", width=25,
                                command=lambda: generate_recommendations_ui(frame))
    generate_button.pack(pady=10)
    
    # Recommendations Display Frame
    rec_frame = ttk.Frame(frame)
    rec_frame.pack(pady=10, padx=20, fill="both", expand=True)

# Function to generate and display recommendations (Need to add live AI functionality and database)
def generate_recommendations_ui(frame):
    """Generates and displays course recommednations (Placeholder need to add functionality with AI and database)"""
    global current_user

    clear_content(frame)
    set_active_button("Recommendations")
    header_label = tk.Label(frame, text = "Course Recommendations", font = ("Helvetica", 14))
    header_label.pack(pady=20)

    # Loading label
    loading_label = tk.Label(frame, text="Generating recommendations, please wait...", font=("Helvetica", 12))
    loading_label.pack(pady=10)
    frame.update()
    
    try:
        required_fields = ["college", "department", "degree_level", "degree", "job"]
        missing_fields = [field for field in required_fields if field not in current_user or not current_user[field]]
        if missing_fields:
            messagebox.showwarning(
                "Incomplete Preferences",
                f"Please complete your preferences before generating recommendations. Missing: {', '.join(missing_fields)}"
            )
            logger.warning(f"Cannot generate recommendations, missing preferences: {missing_fields}")
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
        job_id = 1 # Placeholder job ID

        response = get_recommendations_ai(
            job_id = job_id,
            job_name = job_name,
            degree_name = degree_name,
            degree_electives= degree_electives,
        )

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
    tk.Label(frame, text = "Course Details Page", font = ("Helvetica", 14)).pack(pady=20)

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
    profile_name_label = tk.Label(frame, text=f"Name: {full_name}", font=("Helvetica", 12))
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

            # open db connection
            conn = get_db_connection()
            cursor = conn.cursor()

    # get stored hashed password from db
            cursor.execute("SELECT password_hash FROM users WHERE email = ?", (current_user["email"],))
            row = cursor.fetchone()

            if not row:
                messagebox.showerror("Error", "User record not found in database.", parent=password_window)
                conn.close()
                return

            stored_hash = row[0]

            # verify current password matches the stored hash
            if not bcrypt.checkpw(current_password.encode("utf-8"), stored_hash.encode("utf-8")):
                messagebox.showerror("Error", "Current password is incorrect.", parent=password_window)
                conn.close()
                return

        # confirm new passwords match
            if new_password != confirm_password:
                messagebox.showerror("Error", "New passwords do not match.", parent=password_window)
                conn.close()
                return

            if len(new_password) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters long.", parent=password_window)
                return

            # hash new password
            new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # update password in DB
            cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, current_user["email"]))
            conn.commit()
            conn.close()

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