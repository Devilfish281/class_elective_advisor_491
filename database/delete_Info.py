#delete_Info.py

import sqlite3
#delete use 
def delete_user(user_id, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        
        # Delete the user record
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))


        conn.commit()
        print(f"All data for user {user_id} deleted successfully.")

    except sqlite3.Error as e:
        print(f"Error deleting user data: {e}")

    finally:
        conn.close()

#delete feedbavk individualy, if the feedback is found it useless 
def delete_feedback(feedback_id, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
        conn.commit()
        print(f"Feedback entry {feedback_id} deleted successfully.")

    except sqlite3.Error as e:
        print(f"Error deleting feedback {feedback_id}: {e}")

    finally:
        conn.close()

#delete course
def delete_course(elective_id, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM electives WHERE id = ?", (elective_id,))
        conn.commit()
        print(f"Elective {elective_id} deleted successfully.")

    except sqlite3.Error as e:
        print(f"Error deleting elective {elective_id}: {e}")

    finally:
        conn.close()


