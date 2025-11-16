import sqlite3

#Log in using the user email and password and the data base 
def login_user(email, password_hash, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id FROM users
            WHERE email = ? AND password_hash = ?
        """, (email, password_hash))
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            print(f"Login successful for user ID {user_id}.")
            return user_id
        else:
            print("Login failed: Invalid email or password.")
            return None
    except sqlite3.Error as e:
        print(f"Login error: {e}")
        return None
    finally:
        conn.close()


def search_course(query_string, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, course_code, course_title, description, prerequisites
            FROM electives
            WHERE course_code LIKE ? OR course_title LIKE ? OR description LIKE ?
        """, (f"%{query_string}%", f"%{query_string}%", f"%{query_string}%"))
        results = cursor.fetchall()

        if results:
            print(f"Found {len(results)} matching course(s):")
            for row in results:
                print(f"ID: {row[0]}, Code: {row[1]}, Title: {row[2]}")
                print(f"Description: {row[3]}")
                print(f"Prerequisites: {row[4]}\n")
            return results
        else:
            print("No matching courses found.")
            return []
    except sqlite3.Error as e:
        print(f"Search error: {e}")
        return []
    finally:
        conn.close()


def search_feedback_by_course(query_string, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                feedback.id,
                electives.course_code,
                electives.course_title,
                feedback.comment,
                feedback.rating,
                feedback.timestamp
            FROM feedback
            JOIN electives ON feedback.elective_id = electives.id
            WHERE electives.course_code = ? OR electives.course_title = ?
        """, (query_string, query_string))

        results = cursor.fetchall()

        if results:
            print(f"Found {len(results)} feedback entries for '{query_string}':\n")
            for row in results:
                print(f"Feedback ID: {row[0]}")
                print(f"Course Code: {row[1]}")
                print(f"Course Title: {row[2]}")
                print(f"Comment: {row[3]}")
                print(f"Rating: {row[4]}")
                print(f"Timestamp: {row[5]}\n")
            return results
        else:
            print(f"No feedback found for '{query_string}'.")
            return []
    except sqlite3.Error as e:
        print(f"Search error: {e}")
        return []
    finally:
        conn.close()

import sqlite3

def search_feedback_by_user_id(user_id, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                feedback.id,
                electives.course_code,
                electives.course_title,
                feedback.comment,
                feedback.rating,
                feedback.timestamp
            FROM feedback
            JOIN electives ON feedback.elective_id = electives.id
            WHERE feedback.user_id = ?
        """, (user_id,))

        results = cursor.fetchall()

        if results:
            print(f"Found {len(results)} feedback entries for user ID {user_id}:\n")
            for row in results:
                print(f"Feedback ID: {row[0]}")
                print(f"Course Code: {row[1]}")
                print(f"Course Title: {row[2]}")
                print(f"Comment: {row[3]}")
                print(f"Rating: {row[4]}")
                print(f"Timestamp: {row[5]}\n")
            return results
        else:
            print(f"No feedback found for user ID {user_id}.")
            return []
    except sqlite3.Error as e:
        print(f"Search error: {e}")
        return []
    finally:
        conn.close()

import sqlite3

def search_feedback_by_email(email, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                feedback.id,
                users.email,
                electives.course_code,
                electives.course_title,
                feedback.comment,
                feedback.rating,
                feedback.timestamp
            FROM feedback
            JOIN users ON feedback.user_id = users.id
            JOIN electives ON feedback.elective_id = electives.id
            WHERE users.email = ?
        """, (email,))

        results = cursor.fetchall()

        if results:
            print(f"Found {len(results)} feedback entries for email '{email}':\n")
            for row in results:
                print(f"Feedback ID: {row[0]}")
                print(f"User Email: {row[1]}")
                print(f"Course Code: {row[2]}")
                print(f"Course Title: {row[3]}")
                print(f"Comment: {row[4]}")
                print(f"Rating: {row[5]}")
                print(f"Timestamp: {row[6]}\n")
            return results
        else:
            print(f"No feedback found for email '{email}'.")
            return []
    except sqlite3.Error as e:
        print(f"Search error: {e}")
        return []
    finally:
        conn.close()