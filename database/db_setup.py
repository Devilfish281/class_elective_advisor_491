# database/db_ setup.py
import csv
import logging
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


DB_DIRNAME = "db"  # Added Code
DB_FILENAME = "ai_advice.db"  # Added Code


def create_connection(db_file) -> Optional["sqlite3.Connection"]:
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info("Connected to SQLite database: %s", db_file)
        return conn
    except sqlite3.Error as e:
        logger.error("SQLite connection error: %s", e)
    return conn


def create_tables(conn):
    """Create tables in the SQLite database."""
    try:
        cursor = conn.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")  # Added Code

        # ------------------------------------------------------------------
        # Existing metadata table (kept as-is for your tests / infra)
        # ------------------------------------------------------------------
        cursor.execute(  #  Changed Code
            """
            CREATE TABLE IF NOT EXISTS metadata (
                k TEXT PRIMARY KEY,
                v TEXT
            );
            """
        )

        # ------------------------------------------------------------------
        # Normalized academic structure
        # ------------------------------------------------------------------

        # Colleges
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Colleges (
                college_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
            """
        )

        # Departments
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Departments (
                department_id INTEGER PRIMARY KEY,
                college_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY (college_id)
                    REFERENCES Colleges(college_id)
                    ON DELETE CASCADE
            );
            """
        )

        # Degree levels (e.g. Undergraduate, Graduate)
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Degree_Levels (
                degree_level_id INTEGER PRIMARY KEY,
                department_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY (department_id)
                    REFERENCES Departments(department_id)
                    ON DELETE CASCADE
            );
            """
        )

        # Degrees (e.g. B.S. Computer Science)
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Degrees (
                degree_id INTEGER PRIMARY KEY,
                degree_level_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY (degree_level_id)
                    REFERENCES Degree_Levels(degree_level_id)
                    ON DELETE CASCADE
            );
            """
        )

        # Requirements (e.g. "Major Requirements", "Support Courses")
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Requirements (
                requirement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                degree_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (degree_id)
                    REFERENCES Degrees(degree_id)
                    ON DELETE CASCADE
            );
            """
        )

        # Subcategories (e.g. Lower-Division Core, Upper-Division Core, etc.)
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Subcategories (
                subcategory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (requirement_id)
                    REFERENCES Requirements(requirement_id)
                    ON DELETE CASCADE
            );
            """
        )

        # NOTE from your comment (these are logical examples / seeds, not DDL):
        # 1,1,Lower-Division Core
        # 2,1,Upper-Division Core
        # 3,1,Mathematics Requirements
        # 4,1,Science and Mathematics Electives
        # 5,1,Computer Science Electives

        # Courses table keyed by subcategory (normalized over your old electives)
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subcategory_id INTEGER NOT NULL,
                course_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                units INTEGER NOT NULL DEFAULT 3,
                description TEXT,
                prerequisites TEXT,
                FOREIGN KEY (subcategory_id)
                    REFERENCES Subcategories(subcategory_id)
                    ON DELETE CASCADE
            );
            """
        )

        # Jobs table (target careers, tied to a degree)
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Jobs (
                job_id INTEGER PRIMARY KEY,
                degree_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (degree_id)
                    REFERENCES Degrees(degree_id)
                    ON DELETE CASCADE
            );
            """
        )

        # ------------------------------------------------------------------
        # Existing app tables that your GUI/tests already use
        # ------------------------------------------------------------------

        # users table (kept in lowercase and with the same columns so
        # registration/login/tests keep working)
        cursor.execute(  #  Changed Code
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                specialization TEXT,
                password_hash TEXT NOT NULL
            );
            """
        )

        # electives table (legacy table your tests and db_add.py use)
        cursor.execute(  #  Changed Code
            """
            CREATE TABLE IF NOT EXISTS electives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                course_title TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                credits INTEGER NOT NULL,
                description TEXT,
                prerequisites TEXT
            );
            """
        )

        # feedback table (legacy feedback used by your tests)
        cursor.execute(  #  Changed Code
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                elective_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                rating REAL CHECK(rating >= 0.0 AND rating <= 5.0),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elective_id)
                    REFERENCES electives(id),
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            );
            """
        )

        # ------------------------------------------------------------------
        # New normalized tables that hook into existing users/courses/jobs
        # ------------------------------------------------------------------

        # Prerequisites table referencing course_id instead of course_code
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS Prerequisites (
                prerequisite_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                prerequisite_course_id INTEGER NOT NULL,
                FOREIGN KEY (course_id)
                    REFERENCES Courses(course_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (prerequisite_course_id)
                    REFERENCES Courses(course_id)
                    ON DELETE CASCADE
            );
            """
        )

        # User_Preferences table – ties a user to their academic trajectory
        # NOTE: FK now points to existing users(id) instead of a new Users table.
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS User_Preferences (
                preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                college_id INTEGER,
                department_id INTEGER,
                degree_level_id INTEGER,
                degree_id INTEGER,
                job_id INTEGER,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (college_id)
                    REFERENCES Colleges(college_id),
                FOREIGN KEY (department_id)
                    REFERENCES Departments(department_id),
                FOREIGN KEY (degree_level_id)
                    REFERENCES Degree_Levels(degree_level_id),
                FOREIGN KEY (degree_id)
                    REFERENCES Degrees(degree_id),
                FOREIGN KEY (job_id)
                    REFERENCES Jobs(job_id)
                    ON DELETE SET NULL
            );
            """
        )

        # Recommendations table – redesigned to attach recommendations
        # to users, jobs, and normalized Courses.
        cursor.execute(  #  Changed Code
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                job_id INTEGER,
                course_id INTEGER,
                rating REAL NOT NULL,
                explanation TEXT NOT NULL,
                rank INTEGER,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (job_id)
                    REFERENCES Jobs(job_id)
                    ON DELETE CASCADE,
                FOREIGN KEY (course_id)
                    REFERENCES Courses(course_id)
                    ON DELETE CASCADE
            );
            """
        )

        # User_Interactions – audit trail for what the user did
        cursor.execute(  # Added Code
            """
            CREATE TABLE IF NOT EXISTS User_Interactions (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            );
            """
        )

        conn.commit()
        logger.info("All tables created successfully.")  #  Changed Code

    except sqlite3.Error as e:
        logger.error("An error occurred while creating tables: %s", e)  #  Changed Code
        conn.rollback()


def _get_script_dir() -> str:
    """Helper to get the directory of this script."""
    return os.path.dirname(os.path.abspath(__file__))


def populate_colleges_data(conn):
    """
    Populate the Colleges table from colleges.csv.
    CSV columns: college_id, name
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Colleges;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Colleges table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "colleges.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if "college_id" not in reader.fieldnames or "name" not in reader.fieldnames:
                logger.error("CSV file must contain 'college_id' and 'name' columns.")
                return

            for row in reader:
                college_id = row["college_id"].strip()
                college_name = row["name"].strip()

                if college_id and college_name:
                    if college_id.isdigit():
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO Colleges (college_id, name)
                            VALUES (?, ?);
                            """,
                            (int(college_id), college_name),
                        )
                        logger.info(
                            f"Inserted college: {college_name} with ID: {college_id}"
                        )
                    else:
                        logger.warning(
                            f"Invalid college_id '{college_id}' for college '{college_name}'. Skipping row."
                        )
                else:
                    logger.warning(
                        "Encountered empty 'college_id' or 'name' field. Skipping row."
                    )

        conn.commit()
        logger.info("Colleges table populated from colleges.csv successfully.")

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Colleges: {e}")
        raise


def populate_departments_data(conn):
    """
    Populate the Departments table from departments.csv.
    CSV columns: department_id, college_id, name
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Departments;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Departments table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "departments.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if (
                "department_id" not in reader.fieldnames
                or "college_id" not in reader.fieldnames
                or "name" not in reader.fieldnames
            ):
                logger.error(
                    "CSV file must contain 'department_id', 'college_id', and 'name' columns."
                )
                return

            for row in reader:
                department_id = row["department_id"].strip()
                college_id = row["college_id"].strip()
                department_name = row["name"].strip()

                if department_id and college_id and department_name:
                    if department_id.isdigit() and college_id.isdigit():
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO Departments (department_id, college_id, name)
                            VALUES (?, ?, ?);
                            """,
                            (int(department_id), int(college_id), department_name),
                        )
                        logger.info(
                            f"Inserted department: {department_name} with ID: {department_id} "
                            f"under College ID: {college_id}"
                        )
                    else:
                        logger.warning(
                            f"Invalid department_id '{department_id}' or college_id '{college_id}' "
                            f"for department '{department_name}'. Skipping row."
                        )
                else:
                    logger.warning(
                        "Encountered empty fields in departments.csv. Skipping row."
                    )

        conn.commit()
        logger.info("Departments table populated from departments.csv successfully.")

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Departments: {e}")
        raise


def populate_degree_levels_data(conn):
    """
    Populate the Degree_Levels table from degree_levels.csv.
    CSV columns: degree_level_id, department_id, name
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Degree_Levels;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Degree_Levels table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "degree_levels.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if (
                "degree_level_id" not in reader.fieldnames
                or "department_id" not in reader.fieldnames
                or "name" not in reader.fieldnames
            ):
                logger.error(
                    "CSV file must contain 'degree_level_id', 'department_id', and 'name' columns."
                )
                return

            for row in reader:
                degree_level_id = row["degree_level_id"].strip()
                department_id = row["department_id"].strip()
                degree_level_name = row["name"].strip()

                if degree_level_id and department_id and degree_level_name:
                    if degree_level_id.isdigit() and department_id.isdigit():
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO Degree_Levels (degree_level_id, department_id, name)
                            VALUES (?, ?, ?);
                            """,
                            (
                                int(degree_level_id),
                                int(department_id),
                                degree_level_name,
                            ),
                        )
                        logger.info(
                            f"Inserted degree level: {degree_level_name} with ID: {degree_level_id} "
                            f"under Department ID: {department_id}"
                        )
                    else:
                        logger.warning(
                            f"Invalid degree_level_id '{degree_level_id}' or department_id '{department_id}' "
                            f"for degree level '{degree_level_name}'. Skipping row."
                        )
                else:
                    logger.warning(
                        "Encountered empty fields in degree_levels.csv. Skipping row."
                    )

        conn.commit()
        logger.info(
            "Degree_Levels table populated from degree_levels.csv successfully."
        )

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Degree_Levels: {e}")
        raise


def populate_degrees_data(conn):
    """
    Populate the Degrees table from degrees.csv.
    CSV columns: degree_id, degree_level_id, name
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Degrees;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Degrees table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "degrees.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if (
                "degree_id" not in reader.fieldnames
                or "degree_level_id" not in reader.fieldnames
                or "name" not in reader.fieldnames
            ):
                logger.error(
                    "CSV file must contain 'degree_id', 'degree_level_id', and 'name' columns."
                )
                return

            for row in reader:
                degree_id = row["degree_id"].strip()
                degree_level_id = row["degree_level_id"].strip()
                degree_name = row["name"].strip()

                if degree_id and degree_level_id and degree_name:
                    if degree_id.isdigit() and degree_level_id.isdigit():
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO Degrees (degree_id, degree_level_id, name)
                            VALUES (?, ?, ?);
                            """,
                            (int(degree_id), int(degree_level_id), degree_name),
                        )
                        logger.info(
                            f"Inserted degree: {degree_name} with ID: {degree_id} "
                            f"under Degree Level ID: {degree_level_id}"
                        )
                    else:
                        logger.warning(
                            f"Invalid degree_id '{degree_id}' or degree_level_id '{degree_level_id}' "
                            f"for degree '{degree_name}'. Skipping row."
                        )
                else:
                    logger.warning(
                        "Encountered empty fields in degrees.csv. Skipping row."
                    )

        conn.commit()
        logger.info("Degrees table populated from degrees.csv successfully.")

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Degrees: {e}")
        raise


def populate_requirements_data(conn):
    """
    Populate the Requirements table from requirements.csv.
    CSV columns: requirement_id, degree_id, type, name
    requirement_id is ignored (AUTOINCREMENT); we insert (degree_id, type, name).
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Requirements;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Requirements table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "requirements.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if (
                "requirement_id" not in reader.fieldnames
                or "degree_id" not in reader.fieldnames
                or "type" not in reader.fieldnames
                or "name" not in reader.fieldnames
            ):
                logger.error(
                    "CSV file must contain 'requirement_id', 'degree_id', 'type', and 'name' columns."
                )
                return

            for row in reader:
                degree_id = row["degree_id"].strip()
                req_type = row["type"].strip()
                req_name = row["name"].strip()

                if degree_id and req_type and req_name:
                    if degree_id.isdigit():
                        cursor.execute(
                            """
                            INSERT INTO Requirements (degree_id, type, name)
                            VALUES (?, ?, ?);
                            """,
                            (int(degree_id), req_type, req_name),
                        )
                        logger.info(
                            f"Inserted requirement: {req_name} for Degree ID: {degree_id}"
                        )
                    else:
                        logger.warning(
                            f"Invalid degree_id '{degree_id}' for requirement '{req_name}'. Skipping row."
                        )
                else:
                    logger.warning(
                        "Encountered empty fields in requirements.csv. Skipping row."
                    )

        conn.commit()
        logger.info("Requirements table populated from requirements.csv successfully.")

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Requirements: {e}")
        raise


def populate_subcategories_data(conn):
    """
    Populate the Subcategories table from subcategories.csv.
    CSV columns: subcategory_id, requirement_id, name
    subcategory_id is ignored (AUTOINCREMENT); we insert (requirement_id, name).
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Subcategories;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Subcategories table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "subcategories.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if (
                "subcategory_id" not in reader.fieldnames
                or "requirement_id" not in reader.fieldnames
                or "name" not in reader.fieldnames
            ):
                logger.error(
                    "CSV file must contain 'subcategory_id', 'requirement_id', and 'name' columns."
                )
                return

            for row in reader:
                requirement_id = row["requirement_id"].strip()
                subcat_name = row["name"].strip()

                if requirement_id and subcat_name:
                    if requirement_id.isdigit():
                        cursor.execute(
                            """
                            INSERT INTO Subcategories (requirement_id, name)
                            VALUES (?, ?);
                            """,
                            (int(requirement_id), subcat_name),
                        )
                        logger.info(
                            f"Inserted subcategory: {subcat_name} under Requirement ID: {requirement_id}"
                        )
                    else:
                        logger.warning(
                            f"Invalid requirement_id '{requirement_id}' for subcategory '{subcat_name}'. Skipping row."
                        )
                else:
                    logger.warning(
                        "Encountered empty fields in subcategories.csv. Skipping row."
                    )

        conn.commit()
        logger.info(
            "Subcategories table populated from subcategories.csv successfully."
        )

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Subcategories: {e}")
        raise


def populate_courses_data(conn):
    """
    Populate the Courses table from courses.csv.
    CSV columns: course_id, subcategory_id, name, description, prerequisites
    - 'name' is parsed into (course_code, course_name, units) as:
      "CPSC 120, Introduction to Programming, (3)"
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Courses;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Courses table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "courses.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            required_columns = {
                "course_id",
                "subcategory_id",
                "name",
                "description",
                "prerequisites",
            }
            missing_columns = required_columns - set(reader.fieldnames)
            if missing_columns:
                logger.error(
                    f"CSV file is missing the following required columns: {', '.join(missing_columns)}."
                )
                return

            for row in reader:
                course_id = row["course_id"].strip()
                subcategory_id = row["subcategory_id"].strip()
                full_name = row["name"].strip()
                course_description = row["description"].strip()
                prerequisites = row["prerequisites"].strip()

                course_code = None
                course_name = None
                units = 3  # default

                try:
                    parts = [part.strip() for part in full_name.split(",")]
                    if len(parts) >= 3:
                        course_code = parts[0]
                        course_name = ", ".join(parts[1:-1])
                        units_str = parts[-1].strip("() ")
                        if units_str.isdigit():
                            units = int(units_str)
                        else:
                            logger.warning(
                                f"Invalid units '{units_str}' for course '{course_code}'. "
                                f"Using default units: {units}."
                            )
                    elif len(parts) == 2:
                        course_code = parts[0]
                        course_name = parts[1]
                    else:
                        course_code = parts[0] if parts else None
                        course_name = full_name
                except Exception as e:
                    logger.warning(
                        f"Failed to parse 'name' field '{full_name}' for course_id '{course_id}': {e}. Skipping row."
                    )
                    continue

                if not all([course_id, subcategory_id, course_code, course_name]):
                    logger.warning(
                        "One or more required fields are missing in a row. Skipping row."
                    )
                    continue

                if not (course_id.isdigit() and subcategory_id.isdigit()):
                    logger.warning(
                        f"Invalid data types for course_id '{course_id}' or subcategory_id '{subcategory_id}'. Skipping row."
                    )
                    continue

                cursor.execute(
                    """
                    INSERT INTO Courses (subcategory_id, course_code, name, units, description, prerequisites)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        int(subcategory_id),
                        course_code,
                        course_name,
                        units,
                        course_description,
                        prerequisites,
                    ),
                )
                logger.info(
                    f"Inserted course: {course_name} ({course_code}) under Subcategory ID: {subcategory_id} "
                    f"with units: {units}"
                )

        conn.commit()
        logger.info("Courses table populated from courses.csv successfully.")

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error while populating Courses: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Courses: {e}")
        raise


def populate_jobs_data(conn):
    """
    Populate the Jobs table from jobs.csv.
    CSV columns: job_id, degree_id, name, description
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Jobs;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Jobs table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "jobs.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            required_columns = {"job_id", "degree_id", "name", "description"}
            if not required_columns.issubset(reader.fieldnames):
                logger.error(
                    f"CSV file must contain the following columns: {', '.join(required_columns)}."
                )
                return

            for row in reader:
                job_id = row["job_id"].strip()
                degree_id = row["degree_id"].strip()
                job_name = row["name"].strip()
                job_description = row["description"].strip()

                if job_id and degree_id and job_name:
                    if job_id.isdigit() and degree_id.isdigit():
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO Jobs (job_id, degree_id, name, description)
                            VALUES (?, ?, ?, ?);
                            """,
                            (int(job_id), int(degree_id), job_name, job_description),
                        )
                        logger.info(
                            f"Inserted job: {job_name} with ID: {job_id} under Degree ID: {degree_id}"
                        )
                    else:
                        logger.warning(
                            f"Invalid job_id '{job_id}' or degree_id '{degree_id}' for job '{job_name}'. Skipping row."
                        )
                else:
                    logger.warning(
                        "Encountered empty 'job_id', 'degree_id', or 'name' field in jobs.csv. Skipping row."
                    )

        conn.commit()
        logger.info("Jobs table populated from jobs.csv successfully.")

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error while populating Jobs: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Jobs: {e}")
        raise


def populate_prerequisites_data(conn):
    """
    Populate the Prerequisites table from prerequisites.csv.
    CSV columns: course_code, prerequisite_course_code

    - Looks up course_id and prerequisite_course_id in Courses by course_code.
    - Inserts into Prerequisites (course_id, prerequisite_course_id).
    """
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Prerequisites;")
        count = cursor.fetchone()[0]
        if count > 0:
            logger.info("Prerequisites table already populated. Skipping CSV loading.")
            return

        csv_file_path = os.path.join(_get_script_dir(), "prerequisites.csv")
        if not os.path.isfile(csv_file_path):
            logger.error(
                f"CSV file not found at {csv_file_path}. Please ensure the file exists."
            )
            return

        with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            required_columns = {"course_code", "prerequisite_course_code"}
            if not required_columns.issubset(reader.fieldnames):
                logger.error(
                    f"CSV file must contain the following columns: {', '.join(required_columns)}."
                )
                return

            for row in reader:
                course_code = row["course_code"].strip()
                prereq_code = row["prerequisite_course_code"].strip()

                if not course_code or not prereq_code:
                    logger.warning(
                        "Empty course_code or prerequisite_course_code in prerequisites.csv. Skipping row."
                    )
                    continue

                # Look up IDs for the codes
                cursor.execute(
                    "SELECT course_id FROM Courses WHERE course_code = ?;",
                    (course_code,),
                )
                course_row = cursor.fetchone()
                if not course_row:
                    logger.warning(
                        f"Course with code '{course_code}' not found in Courses table. Skipping row."
                    )
                    continue
                course_id = course_row[0]

                cursor.execute(
                    "SELECT course_id FROM Courses WHERE course_code = ?;",
                    (prereq_code,),
                )
                prereq_row = cursor.fetchone()
                if not prereq_row:
                    logger.warning(
                        f"Prerequisite course with code '{prereq_code}' not found in Courses table. Skipping row."
                    )
                    continue
                prereq_id = prereq_row[0]

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO Prerequisites (course_id, prerequisite_course_id)
                    VALUES (?, ?);
                    """,
                    (course_id, prereq_id),
                )
                logger.info(
                    f"Inserted prerequisite: {course_code} requires {prereq_code} "
                    f"(course_id={course_id}, prerequisite_course_id={prereq_id})"
                )

        conn.commit()
        logger.info(
            "Prerequisites table populated from prerequisites.csv successfully."
        )

    except FileNotFoundError:
        logger.error(
            f"CSV file not found at {csv_file_path}. Please ensure the file exists."
        )
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error while populating Prerequisites: {e}")
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"An error occurred while populating Prerequisites: {e}")
        raise


def populate_all_reference_data(conn):
    """
    Convenience function to populate all core reference tables
    in dependency-safe order.
    """
    populate_colleges_data(conn)
    populate_departments_data(conn)
    populate_degree_levels_data(conn)
    populate_degrees_data(conn)
    populate_requirements_data(conn)
    populate_subcategories_data(conn)
    populate_courses_data(conn)
    populate_jobs_data(conn)
    populate_prerequisites_data(conn)

    logger.info("All reference data population routines have been executed.")


def main_int_db(database: Optional[str] = None) -> None:
    logger.info("Starting database setup...")

    # Always use ./db/ directory
    db_directory = os.path.join(os.getcwd(), DB_DIRNAME)
    if not os.path.exists(db_directory):
        os.makedirs(db_directory, exist_ok=True)
        logger.info("Created directory for database at %s", db_directory)

    # Default to ai_advice.db inside ./db
    if database is None:
        database = DB_FILENAME

    db_path = os.path.join(db_directory, database)

    conn = create_connection(db_path)

    if conn is not None:
        try:
            create_tables(conn)
            populate_all_reference_data(conn)
        except Exception as e:
            logger.error(
                "An error occurred during database setup at %s: %s", db_path, e
            )
            raise
        finally:
            conn.close()
            logger.info("Database setup completed. Database file: %s", db_path)
    else:
        logger.error("Error! Cannot create the database connection.")


def main_test_db(option: int) -> bool:
    """
    DB test dispatcher:
      option 1 -> call main_int_db() (creates db/ai_advice.db)
      option 2 -> in-memory schema test (calls create_tables on ':memory:')
      option 3 -> tempfile smoke test (creates a temp sqlite file, runs simple insert/select)
    Returns True on success, False on failure.
    """
    logger.info("main_test_db: selected option %s", option)

    if option == 1:
        try:
            # Use the same DB file as the app: db/ai_advice.db
            main_int_db()
            logger.info("main_test_db option 1: main_int_db completed successfully.")
            return True
        except Exception:
            logger.exception("main_test_db option 1 failed")
            return False

    elif option == 2:
        conn = None
        try:
            conn = create_connection(":memory:")
            if conn is None:
                logger.error(
                    "main_test_db option 2: failed to create in-memory connection"
                )
                return False
            create_tables(conn)
            logger.info("main_test_db option 2: in-memory create_tables OK")
            return True
        except Exception:
            logger.exception("main_test_db option 2 failed")
            return False
        finally:
            if conn:
                conn.close()

    elif option == 3:
        try:
            fd, tmp_path = tempfile.mkstemp(suffix=".sqlite")
            os.close(fd)
            logger.info("main_test_db option 3: temp DB at %s", tmp_path)
            conn = create_connection(tmp_path)
            if conn is None:
                logger.error(
                    "main_test_db option 3: failed to create temp DB connection"
                )
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                return False
            create_tables(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (k, v) VALUES (?, ?)", ("t", "1")
            )
            conn.commit()
            cursor.execute("SELECT v FROM metadata WHERE k = ?", ("t",))
            r = cursor.fetchone()
            conn.close()
            os.remove(tmp_path)
            ok = r is not None and r[0] == "1"
            if ok:
                logger.info("main_test_db option 3: tempfile smoke test passed")
            else:
                logger.error(
                    "main_test_db option 3: tempfile smoke test failed (unexpected result)"
                )
            return ok
        except Exception:
            logger.exception("main_test_db option 3 failed")
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return False

    else:
        logger.error("main_test_db: unknown option %s", option)
        return False
