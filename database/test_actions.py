
#test_actions.py
#Command you can use in terminal: 
    #pytest test_actions.py
    #python -m pytest test_actions.py

import sqlite3
from db_add import add_user, add_elective, add_feedback
from user_actions import (
    login_user_email,
    search_course,
    search_feedback_by_course,
    search_feedback_by_user_id,
    search_feedback_by_email
)

DB_PATH = "ai_advice.db"

# Create a test user with a unique email
import uuid
def create_test_user():
    unique_email = f"testuser_{uuid.uuid4().hex}@example.com"
    return add_user(
        first_name="Test",
        last_name="User",
        email=unique_email,
        phone="123-456-7890",
        specialization="AI",
        password_hash="securepass123"
    )

# Create a test elective
def create_test_elective():
    return add_elective(
        course_code="CPSC 254",
        course_title="Software Dev with OSS",
        category_id=1,
        credits=3,
        description="Open source tools",
        prerequisites="CPSC 121"
    )

#Create a test feedback
def create_test_feedback(user_id, elective_id):
    return add_feedback(
        user_id=user_id,
        elective_id=elective_id,
        comment="Great course!",
        rating=5
    )

#Test: login_user
def test_login_user():
    user_id = create_test_user()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    email = cursor.fetchone()[0]
    conn.close()
    result = login_user_email(email, "securepass123")
    assert result == user_id

# Test: search_course
def test_search_course():
    elective_id = create_test_elective()
    results = search_course("CPSC 254")
    assert isinstance(results, list)
    assert any(row[0] == elective_id for row in results)

#Test: search_feedback_by_course
def test_search_feedback_by_course():
    user_id = create_test_user()
    elective_id = create_test_elective()
    feedback_id = create_test_feedback(user_id, elective_id)
    results = search_feedback_by_course("CPSC 254")
    assert isinstance(results, list)
    assert any(row[0] == feedback_id for row in results)

#Test: search_feedback_by_user_id 
def test_search_feedback_by_user():
    user_id = create_test_user()
    elective_id = create_test_elective()
    feedback_id = create_test_feedback(user_id, elective_id)
    results = search_feedback_by_user_id(user_id)
    assert isinstance(results, list)
    assert any(row[0] == feedback_id for row in results)

# Test: search_feedback_by_email
def test_search_feedback_by_email():
    user_id = create_test_user()
    elective_id = create_test_elective()
    feedback_id = create_test_feedback(user_id, elective_id)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    email = cursor.fetchone()[0]
    conn.close()

    results = search_feedback_by_email(email)
    assert isinstance(results, list)
    assert any(row[0] == feedback_id for row in results)