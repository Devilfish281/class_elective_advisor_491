#edit_info.py 

import sqlite3

#change pasword 
def change_password(user_id, new_password, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (new_password, user_id))
        conn.commit()
        print(f"Password updated for user {user_id}.")
    except sqlite3.Error as e:
        print(f"Error updating password: {e}")
    finally:
        conn.close()

#change specialization
def change_specialization(user_id, new_specialization, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE users
            SET specialization = ?
            WHERE id = ?
        """, (new_specialization, user_id))
        conn.commit()
        print(f"Specialization updated for user {user_id}.")
    except sqlite3.Error as e:
        print(f"Error updating specialization: {e}")
    finally:
        conn.close()

#change prerequisites
def change_prerequisites(elective_id, new_prerequisites, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE electives
            SET prerequisites = ?
            WHERE id = ?
        """, (new_prerequisites, elective_id))
        conn.commit()
        print(f"Prerequisites updated for elective {elective_id}.")
    except sqlite3.Error as e:
        print(f"Error updating prerequisites: {e}")
    finally:
        conn.close()

