import sqlite3


#thisline of code create a connection in sqlite3
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
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        credits INTEGER NOT NULL,
        description TEXT,
        prerequisites TEXT
    )
    """)

    conn.commit()
    print("Users table created successfully.")

except sqlite3.Error as e:
    print(f"SQLite error: {e}")

finally:
    if conn:
        conn.close()
