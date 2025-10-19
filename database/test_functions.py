#test_functions.py
#Command you can use in terminal: 
    #pytest test_functions.py
    #python -m pytest test_functions.py

"""They simulate real-world usage by creating test data, performing operations, and asserting expected outcomes — ensuring your logic is reliable,
 isolated, and future-proof."""

import sqlite3
from db_add import add_user, add_elective, add_feedback
from delete_Info import delete_user, delete_feedback, delete_course
from edit_info import change_password, change_specialization, change_prerequisites
import uuid

DB_PATH = "ai_advice.db"

#Utility: create a test user
#Purpose: Adds a new user with a unique email to avoid conflicts.
#How it works: Uses uuid to generate a unique email, then calls add_user() with static values.
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
#Utility: create a test elective
#Purpose: Adds a sample elective to test feedback and course-related operations.
#How it works: Calls add_elective() with fixed course details.
def create_test_elective():
    return add_elective(
        course_code="CPSC 254", 
        course_title="Software Dev with OSS",
        category_id=1,
        credits=3,
        description="Open source tools",
        prerequisites="CPSC 121"
    )

# Utility: create a test feedback
#Purpose: Adds feedback for a given user and elective.
#How it works: Calls add_feedback() with static comment and rating.
def create_test_feedback(user_id, elective_id):
    return add_feedback(
        user_id=user_id,
        elective_id=elective_id,
        comment="Great course!",
        rating=5
    )
# ---> Tests: confirm that data is correctly inserted into the database.

#Purpose: Verifies that a user is successfully added.
#How it works: Asserts that the returned user_id is an integer.
def test_add_user():
    user_id = create_test_user()
    assert isinstance(user_id, int)

#Purpose: Verifies that an elective is successfully added.
#How it works: Asserts that the returned elective_id is an integer.
def test_add_elective():
    elective_id = create_test_elective()
    assert isinstance(elective_id, int)

#Purpose: Verifies that feedback is successfully added.
#How it works: Asserts that the returned feedback_id is not None, meaning the insert succeeded.
def test_add_feedback():
    user_id = create_test_user()
    elective_id = create_test_elective()
    feedback_id = create_test_feedback(user_id, elective_id)
    print("Feedback ID:", feedback_id)
    assert feedback_id is not None

# ---> Edit Tests: confirm that updates to existing records are correctly applied.

#Purpose: Verifies that a user's password is updated.
#How it works: Changes the password, queries the DB, and asserts the new value.
def test_change_password():
    user_id = create_test_user()
    change_password(user_id, "newpass123")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
    assert cursor.fetchone()[0] == "newpass123"
    conn.close()

#Purpose: Verifies that a user's specialization is updated.
#How it works: Updates the specialization and checks the DB for the new value.
def test_change_specialization():
    user_id = create_test_user()
    change_specialization(user_id, "Robotics")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT specialization FROM users WHERE id = ?", (user_id,))
    assert cursor.fetchone()[0] == "Robotics"
    conn.close()

#Purpose: Verifies that an elective's prerequisites are updated.
#How it works: Updates the prerequisites and asserts the change.
def test_change_prerequisites():
    elective_id = create_test_elective()
    change_prerequisites(elective_id, "CPSC 101")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT prerequisites FROM electives WHERE id = ?", (elective_id,))
    assert cursor.fetchone()[0] == "CPSC 101"
    conn.close()

# ---> Delete Tests: confirm that records are properly removed from the database.

#Purpose: Verifies that a user is deleted.
#How it works: Deletes the user and asserts that no record remains.
def test_delete_user():
    user_id = create_test_user()
    delete_user(user_id)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    assert cursor.fetchone() is None
    conn.close()

#Purpose: Verifies that feedback is deleted.
#How it works: Deletes the feedback and checks that it's gone.
def test_delete_feedback():
    user_id = create_test_user()
    elective_id = create_test_elective()
    feedback_id = create_test_feedback(user_id, elective_id)
    delete_feedback(feedback_id)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,))
    assert cursor.fetchone() is None
    conn.close()

#Purpose: Verifies that an elective is deleted.
#How it works: Deletes the elective and asserts that no record remains.
def test_delete_course():
    elective_id = create_test_elective()
    delete_course(elective_id)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM electives WHERE id = ?", (elective_id,))
    assert cursor.fetchone() is None
    conn.close()

#Why These Tests Matter
    #Isolation: Each test creates its own data, so they don’t interfere with each other.
    #Validation: They confirm that your SQL logic works as expected.
    #Regression-proofing: If future changes break something, these tests will catch it.
    #Scalability: You can extend this suite to cover edge cases, constraints, and joins.
