
#db_add.py
#this file will contain way for the user and system to add infonmation or update the infomation

import sqlite3

#add user (Register)
def add_user(first_name, last_name, email, phone, specialization, password_hash):
    conn = sqlite3.connect("ai_advice.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (first_name, last_name, email, phone, specialization, password_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (first_name, last_name, email, phone, specialization, password_hash))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

#add a new elective
def add_elective(course_code, course_title, category_id, credits, description, prerequisites, db_path="ai_advice.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO electives (course_code, course_title, category_id, credits, description, prerequisites)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (course_code, course_title, category_id, credits, description, prerequisites))

    conn.commit()
    elective_id = cursor.lastrowid
    conn.close()
    return elective_id

#add feedback
def add_feedback(user_id, elective_id, course_code, comment, rating):
    conn = sqlite3.connect("ai_advice.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (user_id, elective_id, course_code, comment, rating)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, elective_id, course_code, comment, rating))
    conn.commit()
    conn.close()

