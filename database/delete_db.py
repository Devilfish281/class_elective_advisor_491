
#delete_db.py
import os
#if changeges are made this can delete the data base
file_path = r"ai_advice.db"

try:
    if os.path.exists(file_path):
        os.remove(file_path)
        print("ai_advice.db deleted successfully.")
    else:
        print("File not found.")
except Exception as e:
    print(f"Error deleting file: {e}")