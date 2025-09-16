import sqlite3
import csv

#db connection 
conn = sqlite3.connect("ai_advice.db")
cursor = conn.cursor()

#read and openn file 
with open(r"C:\Users\alexa\Desktop\490\class_elective_advisor_491\database\courses.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        cursor.execute("""
        INSERT INTO electives (category, credits, title, description, prerequisites)
        VALUES (?, ?, ?, ?, ?)
        """, (
            row['category(id)'],
            int(row['credits']),
            row['title'],
            row['description'],
            row['prerequisites']
        ))

conn.commit()
conn.close()
print("Electives imported successfully.")