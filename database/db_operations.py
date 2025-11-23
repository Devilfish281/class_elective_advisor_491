# database/db_operations.py
import logging
import os
import sqlite3
from typing import Optional

DB_DIRNAME = "db"
DB_FILENAME = "ai_advice.db"


logger = logging.getLogger(__name__)  # Reuse the global logger


def connect_db():
    database = DB_FILENAME  # Default database name

    # Define the db directory path (at the current level)
    db_directory = os.path.join(os.getcwd(), DB_DIRNAME)
    # Define the database path inside the db directory
    db_path = os.path.join(db_directory, database)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        logger.debug(f"Connected to database at {db_path}.")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


"""
These functions retrieve data based on user selections to populate the dropdowns dynamically.

Fetching Data for Dropdowns:

get_colleges(): Retrieves all colleges.
get_departments(college_id): Retrieves departments under a specific college.
get_degree_levels(department_id): Retrieves degree levels under a specific department.
get_degrees(degree_level_id): Retrieves degrees under a specific degree level.
"""


def get_colleges():
    logger.info("Starting get colleges")

    """Fetches all colleges from the Colleges table."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT college_id, name FROM Colleges ORDER BY name;")
        colleges = cursor.fetchall()
        conn.close()
        return colleges
    except sqlite3.Error as e:
        logger.error(f"Error fetching colleges: {e}")
        return []


def get_departments(college_id):
    """Fetches departments based on the selected college."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT department_id, name FROM Departments WHERE college_id = ? ORDER BY name;",
            (college_id,),
        )
        departments = cursor.fetchall()
        conn.close()
        return departments
    except sqlite3.Error as e:
        logger.error(f"Error fetching departments for college_id {college_id}: {e}")
        return []


def get_degree_levels(department_id):
    """Fetches degree levels based on the selected department."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT degree_level_id, name FROM Degree_Levels WHERE department_id = ? ORDER BY name;",
            (department_id,),
        )
        degree_levels = cursor.fetchall()
        conn.close()
        return degree_levels
    except sqlite3.Error as e:
        logger.error(
            f"Error fetching degree levels for department_id {department_id}: {e}"
        )
        return []


def get_degrees(degree_level_id):
    """Fetches degrees based on the selected degree level."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT degree_id, name FROM Degrees WHERE degree_level_id = ? ORDER BY name;",
            (degree_level_id,),
        )
        degrees = cursor.fetchall()
        conn.close()
        return degrees
    except sqlite3.Error as e:
        logger.error(
            f"Error fetching degrees for degree_level_id {degree_level_id}: {e}"
        )
        return []


def get_jobs_by_degree(degree_id):
    """
    Retrieves all jobs associated with a specific degree.

    Parameters:
        degree_id (int): The ID of the degree.

    Returns:
        list of dict: A list of jobs with their details.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT job_id, name, description
            FROM Jobs
            WHERE degree_id = ?
            ORDER BY name;
            """,
            (degree_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        jobs = []
        for row in rows:
            jobs.append(
                {
                    "job_id": row["job_id"],
                    "name": row["name"],
                    "description": row["description"],
                }
            )
        logger.info(f"Fetched {len(jobs)} jobs for degree_id {degree_id}.")
        return jobs

    except sqlite3.Error as e:
        logger.error(f"Error fetching jobs for degree_id {degree_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching jobs for degree_id {degree_id}: {e}")
        return []


def update_user_preferences(user_id, student_id=None, gpa=None):
    """
    Updates a user's student_id and/or gpa in the User_Preferences table.

    Parameters:
        user_id (int): The user's unique identifier.
        student_id (str, optional): New student ID to update.
        gpa (float, optional): New GPA to update.

    Returns:
        bool: True if update is successful, False otherwise.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Update student_id if provided
        if student_id:
            cursor.execute(
                """
                UPDATE User_Preferences
                SET student_id = ?
                WHERE user_id = ?;
                """,
                (student_id, user_id),
            )
            logger.info(f"Updated student_id for user_id: {user_id} to {student_id}")

        # Update gpa if provided
        if gpa is not None:
            cursor.execute(
                """
                UPDATE User_Preferences
                SET gpa = ?
                WHERE user_id = ?;
                """,
                (gpa, user_id),
            )
            logger.info(f"Updated gpa for user_id: {user_id} to {gpa}")

        conn.commit()
        return True

    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Database Error during updating user preferences: {e}")
        return False
    except Exception as e:
        conn.rollback()
        logger.error(f"Unexpected error during updating user preferences: {e}")
        return False
    finally:
        conn.close()


"""
get and update user preferences

Saving User Preferences:
save_user_preferences(user_id, preferences): 
Saves or updates the user's preferences. It checks if the user already has a preferences entry and updates it; otherwise, it inserts a new entry.


Retrieving User Preferences:
get_user_preferences(user_id): Fetches the user's current preferences to pre-populate the dropdowns in the UI.
"""


def save_user_preferences(user_id, preferences):
    """
    Saves user preferences to the User_Preferences table.

    Parameters:
        user_id (int): The ID of the user.
        preferences (dict): A dictionary containing preference IDs with keys:
                            'college_id', 'department_id', 'degree_level_id', 'degree_id', 'job_id'

    Returns:
        bool: True if preferences are saved successfully, False otherwise.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if the user already has preferences set
        cursor.execute(
            "SELECT preference_id FROM User_Preferences WHERE user_id = ?;",
            (user_id,),
        )
        row = cursor.fetchone()

        if row:
            # Update existing preferences
            cursor.execute(
                """
                UPDATE User_Preferences
                SET college_id = ?, department_id = ?, degree_level_id = ?, degree_id = ?, job_id = ?
                WHERE user_id = ?;
                """,
                (
                    preferences.get("college_id"),
                    preferences.get("department_id"),
                    preferences.get("degree_level_id"),
                    preferences.get("degree_id"),
                    preferences.get("job_id"),
                    user_id,
                ),
            )
            logger.info(f"Updated preferences for user_id {user_id}.")
        else:
            # Insert new preferences
            cursor.execute(
                """
                INSERT INTO User_Preferences (user_id, college_id, department_id, degree_level_id, degree_id, job_id)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    user_id,
                    preferences.get("college_id"),
                    preferences.get("department_id"),
                    preferences.get("degree_level_id"),
                    preferences.get("degree_id"),
                    preferences.get("job_id"),
                ),
            )
            logger.info(f"Inserted preferences for user_id {user_id}.")

        conn.commit()
        conn.close()
        return True

    except sqlite3.Error as e:
        logger.error(f"Error saving preferences for user_id {user_id}: {e}")
        conn.rollback()
        conn.close()
        return False


def get_user_preferences(user_id):
    """
    Retrieves user preferences from the User_Preferences table.

    Parameters:
        user_id (int): The ID of the user.

    Returns:
        dict: A dictionary containing preference IDs with keys:
              'college_id', 'department_id', 'degree_level_id', 'degree_id', 'job_id'
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT college_id, department_id, degree_level_id, degree_id, job_id
            FROM User_Preferences
            WHERE user_id = ?;
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            preferences = {
                "college_id": row["college_id"],
                "department_id": row["department_id"],
                "degree_level_id": row["degree_level_id"],
                "degree_id": row["degree_id"],
                "job_id": row["job_id"],
            }
            return preferences
        else:
            return {}
    except sqlite3.Error as e:
        logger.error(f"Error fetching preferences for user_id {user_id}: {e}")
        return {}


def clear_recommendations(user_id, job_id):
    """
    Deletes all course recommendations for a specific user and job from the Recommendations table.

    Parameters:
        user_id (int): The ID of the user whose recommendations are to be cleared.
        job_id (int): The ID of the job associated with the recommendations to be cleared.

    Returns:
        bool: True if the deletion is successful, False otherwise.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM Recommendations
            WHERE user_id = ? AND job_id = ?;
            """,
            (user_id, job_id),
        )
        deleted_rows = cursor.rowcount  # Number of rows deleted
        conn.commit()
        conn.close()
        if deleted_rows > 0:
            logger.info(
                f"Cleared {deleted_rows} recommendation(s) for user_id {user_id} and job_id {job_id}."
            )
            return True
        else:
            logger.info(
                f"No recommendations found for user_id {user_id} and job_id {job_id} to clear."
            )
            return False
    except sqlite3.Error as e:
        logger.error(
            f"Database error while clearing recommendations for user_id {user_id} and job_id {job_id}: {e}"
        )
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error while clearing recommendations for user_id {user_id} and job_id {job_id}: {e}"
        )
        if conn:
            conn.close()
        return False


def get_course_id_by_code(course_code):
    """
    Retrieves the course_id for a given course_code from the Courses table.

    Parameters:
        course_code (str): The code of the course.

    Returns:
        int or None: The course_id if found, else None.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT course_id FROM Courses WHERE course_code = ?", (course_code,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return result["course_id"]
        else:
            logger.warning(f"Course code '{course_code}' not found in Courses table.")
            return None
    except sqlite3.Error as e:
        logger.error(
            f"Database error while looking up course_id for '{course_code}': {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error while looking up course_id for '{course_code}': {e}"
        )
        return None


def save_recommendation(user_id, job_id, course_id, rating, explanation, rank):
    """
    Saves a single recommendation to the Recommendations table.

    :param user_name: string , The ID of the user.
    :param job_id: int, The ID of the job.
    :param course_code (str): The code of the course, e.g., "CPSC 120".
    :param rating: float, The rating of the recommendation.
    :param explanation: str, The explanation for the recommendation.
    :param rank: int, The rank of the recommendation.
    :return: bool, True if saved successfully, False otherwise.
    """
    try:
        # Lookup course_id using the course_code
        # course_id = get_course_id_by_code(course_code)
        if course_id is None:
            logger.error(
                f"Failed to save recommendation: Course code '{course_code}' not found."
            )
            return False

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Recommendations (user_id, job_id, course_id, rating, explanation, rank)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, job_id, course_id, rating, explanation, rank),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving recommendation: {e}")
        return False


def get_recommendations(user_id, job_id):
    """
    Retrieves all course recommendations for a specific user and job from the Recommendations table,
    including detailed course information from the Courses table.

    Parameters:
        user_id (int): The ID of the user whose recommendations are to be retrieved.
        job_id (int): The ID of the job associated with the recommendations.

    Returns:
        list of dict: A list of dictionaries, each containing detailed information about a recommended course.
                      Returns an empty list if no recommendations are found.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Debug Fetch and count all records from the Recommendations table
        cursor.execute("SELECT * FROM Recommendations")
        all_records = cursor.fetchall()
        record_count = len(all_records)
        logger.info(f"Total records in Recommendations table: {record_count}")

        #  Debug Fetch all records with the specified user_id and job_id
        cursor.execute(
            "SELECT * FROM Recommendations WHERE user_id = ? AND job_id = ?",
            (user_id, job_id),
        )
        all_records = cursor.fetchall()
        record_count = len(all_records)
        logger.info(
            f"Total records for user_id {user_id} and job_id {job_id}: {record_count}"
        )

        # Log the details of the first record, if it exists
        if all_records:
            first_record = all_records[0]
            logger.info(
                f"First record - recommendation_id: {first_record['recommendation_id']}, "
                f"user_id: {first_record['user_id']}, job_id: {first_record['job_id']}, "
                f"course_id: {first_record['course_id']}, rating: {first_record['rating']}, "
                f"explanation: {first_record['explanation']}, rank: {first_record['rank']}"
            )

        # The Code Starts here
        # SQL query to join Recommendations and Courses tables to get detailed course information
        cursor.execute(
            """
            SELECT 
                r.course_id,
                c.course_code,
                c.name AS course_name,
                c.units,
                c.prerequisites,
                r.rating,
                r.explanation,
                r.rank
            FROM Recommendations r
            JOIN Courses c ON r.course_id = c.course_id
            WHERE r.user_id = ? AND r.job_id = ?
            ORDER BY r.rank ASC;  -- Assuming lower rank numbers are higher priority
            """,
            (user_id, job_id),
        )

        rows = cursor.fetchall()
        conn.close()

        recommendations = []
        for row in rows:
            recommendations.append(
                {
                    "Course ID": row["course_id"],
                    "Course Code": row["course_code"],
                    "Course Name": row["course_name"],
                    "Units": row["units"],
                    "Prerequisites": row["prerequisites"],
                    "Rating": row["rating"],
                    "Explanation": row["explanation"],
                    "Rank": row["rank"],
                }
            )

        if recommendations:
            logger.info(
                f"Retrieved {len(recommendations)} recommendation(s) for user_id {user_id} and job_id {job_id}."
            )
        else:
            logger.info(
                f"No recommendations found for user_id {user_id} and job_id {job_id}."
            )

        return recommendations

    except sqlite3.Error as e:
        logger.error(
            f"Database error while retrieving recommendations for user_id {user_id} and job_id {job_id}: {e}"
        )
        if conn:
            conn.close()
        return []
    except Exception as e:
        logger.error(
            f"Unexpected error while retrieving recommendations for user_id {user_id} and job_id {job_id}: {e}"
        )
        if conn:
            conn.close()
        return []


def get_job_by_id(job_id):
    """
    Retrieves job details based on job_id.

    :param job_id: int, The ID of the job.
    :return: dict or None, Job details if found, else None.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM Jobs WHERE job_id = ?
            """,
            (job_id,),
        )
        job = cursor.fetchone()
        return job
    except Exception as e:
        logger.error(f"Error fetching job by id {job_id}: {e}")
        return None


def get_degree_by_id(degree_id):
    """
    Retrieves degree details based on degree_id.

    :param degree_id: int, The ID of the degree.
    :return: dict or None, Degree details if found, else None.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM Degrees WHERE degree_id = ?
            """,
            (degree_id,),
        )
        degree = cursor.fetchone()
        return degree
    except Exception as e:
        logger.error(f"Error fetching degree by id {degree_id}: {e}")
        return None


def get_course_by_code(course_code):
    """
    Retrieves course details based on course_code.

    :param course_code: str, The code of the course.
    :return: dict or None, Course details if found, else None.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM Courses WHERE course_code = ?
            """,
            (course_code,),
        )
        course = cursor.fetchone()
        return course
    except Exception as e:
        logger.error(f"Error fetching course by code {course_code}: {e}")
        return None


def get_degree_electives(degree_id):
    """
    Retrieves elective courses specific to a given degree.

    Parameters:
        degree_id (int): The ID of the degree.

    Returns:
        list of dict: A list of elective courses with their details.
    """
    try:
        conn = connect_db()
        cursor = conn.cursor()
        # Assuming subcategory_id 5 corresponds to Computer Science Electives
        # Adjust the subcategory_id as per your database schema
        # TODO: Replace with the correct subcategory_id if different
        # subcategory_id = 5 correctly represents Computer Science Electives in my database
        # Replace '5' with the correct subcategory_id if different
        subcategory_id = (
            5  # Assuming subcategory_id 5 corresponds to Computer Science Electives
        )

        cursor.execute(
            """
            SELECT course_id, course_code, name, units, description, prerequisites
            FROM Courses
            WHERE subcategory_id = ?
            ORDER BY name;
            """,
            (subcategory_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        electives = []
        for row in rows:
            electives.append(
                {
                    "course_id": row["course_id"],
                    "course_code": row["course_code"],
                    "name": row["name"],
                    "units": row["units"],
                    "description": row["description"],
                    "prerequisites": row["prerequisites"],
                }
            )
        logger.info(f"Fetched {len(electives)} electives for degree_id {degree_id}.")
        return electives

    except sqlite3.Error as e:
        logger.error(f"Error fetching degree electives for degree_id {degree_id}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching degree electives: {e}")
        return []
