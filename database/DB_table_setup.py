
import sqlite3


#this line of code create a connection in sqlite3
#ai_advice.db
try:
    conn = sqlite3.connect("ai_advice.db")
    cursor = conn.cursor()

    #user table 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        specialization TEXT,
        password_hash TEXT NOT NULL
    )
    """)

    #elective table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS electives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL,
        course_title TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        credits INTEGER NOT NULL,
        description TEXT,
        prerequisites TEXT
        )
    """)
    #feedback table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        elective_id INTEGER NOT NULL,
        elective_code TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        comment TEXT NOT NULL,
        rating REAL CHECK(rating >= 0.0 AND rating <= 5.0),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (elective_id) REFERENCES electives(id),
        FOREIGN KEY (elective_code) REFERENCES electives(code),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    print("Tables created successfully.")

except sqlite3.Error as e:
    print(f"SQLite error: {e}")

finally:
    if conn:
        conn.close()
