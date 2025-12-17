# tests/test_db_operations.py
# poetry run pytest -q tests/test_db_operations.py


import sqlite3
import uuid

import pytest

from database import db_operations


@pytest.fixture
def in_memory_db(monkeypatch):
    """
    Shared in-memory SQLite DB for a single test.

    - Each test gets a UNIQUE URI so we never collide with a previous run.
    - `keeper_conn` stays open for the whole test (yield) so the DB exists.
    - Production code uses db_operations.connect_db(), which is monkeypatched
      to open NEW connections to the same URI; those can be closed freely.
    """
    # 1) Unique URI per test so there is no cross-test contamination
    unique_name = uuid.uuid4().hex
    db_uri = f"file:ai_advice_test_{unique_name}?mode=memory&cache=shared"

    # Keep one connection alive so the shared in-memory DB exists
    keeper_conn = sqlite3.connect(db_uri, uri=True)
    keeper_conn.row_factory = sqlite3.Row

    # 2) Monkeypatch connect_db to open new connections to this same URI
    def _test_connect_db():
        conn = sqlite3.connect(db_uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(db_operations, "connect_db", _test_connect_db)

    # 3) Create schema + seed data using the keeper connection
    cursor = keeper_conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE Colleges (
            college_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE Departments (
            department_id INTEGER PRIMARY KEY,
            college_id INTEGER NOT NULL,
            name TEXT NOT NULL
        );
        CREATE TABLE Degree_Levels (
            degree_level_id INTEGER PRIMARY KEY,
            department_id INTEGER NOT NULL,
            name TEXT NOT NULL
        );
        CREATE TABLE Degrees (
            degree_id INTEGER PRIMARY KEY,
            degree_level_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            subcategory_id INTEGER
        );
        CREATE TABLE Jobs (
            job_id INTEGER PRIMARY KEY,
            degree_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT
        );
        CREATE TABLE User_Preferences (
            preference_id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            student_id TEXT,
            gpa REAL,
            college_id INTEGER,
            department_id INTEGER,
            degree_level_id INTEGER,
            degree_id INTEGER,
            job_id INTEGER
        );
        CREATE TABLE Courses (
            course_id INTEGER PRIMARY KEY,
            course_code TEXT NOT NULL,
            name TEXT NOT NULL,
            units INTEGER,
            description TEXT,
            prerequisites TEXT,
            subcategory_id INTEGER
        );
        CREATE TABLE Recommendations (
            recommendation_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            rating REAL,
            explanation TEXT,
            rank INTEGER
        );
        """
    )

    # ---- Seed data (values match what your tests now expect) ----
    cursor.execute(
        "INSERT INTO Colleges (college_id, name) VALUES (?, ?);",
        (1, "College of ECS"),
    )

    cursor.execute(
        "INSERT INTO Departments (department_id, college_id, name) VALUES (?, ?, ?);",
        (1, 1, "Computer Science"),
    )

    cursor.execute(
        "INSERT INTO Degree_Levels (degree_level_id, department_id, name) "
        "VALUES (?, ?, ?);",
        (1, 1, "Undergraduate"),
    )

    cursor.execute(
        "INSERT INTO Degrees (degree_id, degree_level_id, name, subcategory_id) "
        "VALUES (?, ?, ?, ?);",
        (1, 1, "B.S. Computer Science", 5),
    )

    cursor.execute(
        "INSERT INTO Jobs (job_id, degree_id, name, description) "
        "VALUES (?, ?, ?, ?);",
        (1, 1, "Software Engineer", "Builds and maintains software systems."),
    )

    cursor.execute(
        """
        INSERT INTO User_Preferences (
            preference_id, user_id, student_id, gpa,
            college_id, department_id, degree_level_id, degree_id, job_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (1, 42, "TEST123", 3.5, 1, 1, 1, 1, 1),
    )

    cursor.execute(
        """
        INSERT INTO Courses (
            course_id, course_code, name, units, description, prerequisites, subcategory_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            1,
            "CPSC 120",
            "Introduction to Programming",
            3,
            "Intro to programming in a high-level language.",
            "None",
            5,
        ),
    )

    cursor.execute(
        """
        INSERT INTO Recommendations (
            recommendation_id, user_id, job_id, course_id, rating, explanation, rank
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (1, 42, 1, 1, 4.5, "Recommended core elective.", 1),
    )

    keeper_conn.commit()

    # Yield keeper_conn so tests can run additional direct SQL checks
    try:
        yield keeper_conn
    finally:
        keeper_conn.close()


# --- Tests for basic dropdown queries ---


def test_get_colleges_returns_seeded_college(in_memory_db):
    colleges = db_operations.get_colleges()
    assert len(colleges) == 1
    assert colleges[0]["college_id"] == 1
    assert colleges[0]["name"] == "College of ECS"


def test_get_departments_filters_by_college(in_memory_db):
    departments = db_operations.get_departments(1)
    assert len(departments) == 1
    assert departments[0]["department_id"] == 1
    assert departments[0]["name"] == "Computer Science"


def test_get_degree_levels_filters_by_department(in_memory_db):
    degree_levels = db_operations.get_degree_levels(1)
    assert len(degree_levels) == 1
    assert degree_levels[0]["degree_level_id"] == 1
    assert degree_levels[0]["name"] == "Undergraduate"


def test_get_degrees_filters_by_degree_level(in_memory_db):
    degrees = db_operations.get_degrees(1)
    assert len(degrees) == 1
    assert degrees[0]["degree_id"] == 1
    assert degrees[0]["name"] == "B.S. Computer Science"


# --- Tests for jobs and preferences ---


def test_get_jobs_by_degree_returns_jobs(in_memory_db):
    jobs = db_operations.get_jobs_by_degree(1)
    assert len(jobs) == 1
    job = jobs[0]
    assert job["job_id"] == 1
    assert job["name"] == "Software Engineer"
    assert "maintains software systems" in job["description"]


def test_get_user_preferences_returns_seeded_preferences(in_memory_db):
    prefs = db_operations.get_user_preferences(42)
    assert prefs["college_id"] == 1
    assert prefs["department_id"] == 1
    assert prefs["degree_level_id"] == 1
    assert prefs["degree_id"] == 1
    assert prefs["job_id"] == 1


def test_save_user_preferences_updates_existing_row(in_memory_db):
    new_prefs = {
        "college_id": 1,
        "department_id": 1,
        "degree_level_id": 1,
        "degree_id": 1,
        "job_id": 1,
    }

    ok = db_operations.save_user_preferences(42, new_prefs)
    assert ok is True

    # Confirm updated/exists
    prefs = db_operations.get_user_preferences(42)
    assert prefs["college_id"] == 1
    assert prefs["job_id"] == 1


def test_update_user_preferences_changes_student_id_and_gpa(in_memory_db):
    ok = db_operations.update_user_preferences(user_id=42, student_id="NEWID", gpa=3.9)
    assert ok is True

    cursor = in_memory_db.cursor()
    cursor.execute(
        "SELECT student_id, gpa FROM User_Preferences WHERE user_id = ?;",
        (42,),
    )
    row = cursor.fetchone()
    assert row["student_id"] == "NEWID"
    assert pytest.approx(row["gpa"], 0.001) == 3.9


# --- Recommendations tests ---


def test_clear_recommendations_deletes_rows(in_memory_db):
    # Sanity check: we seeded one recommendation for (42,1)
    cursor = in_memory_db.cursor()
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM Recommendations WHERE user_id = ? AND job_id = ?;",
        (42, 1),
    )
    assert cursor.fetchone()["cnt"] == 1

    ok = db_operations.clear_recommendations(42, 1)
    assert ok is True

    cursor.execute(
        "SELECT COUNT(*) as cnt FROM Recommendations WHERE user_id = ? AND job_id = ?;",
        (42, 1),
    )
    assert cursor.fetchone()["cnt"] == 0

    # Second call should find nothing and return False
    ok2 = db_operations.clear_recommendations(42, 1)
    assert ok2 is False


def test_get_course_id_by_code_returns_correct_id(in_memory_db):
    course_id = db_operations.get_course_id_by_code("CPSC 120")
    assert course_id == 1


def test_save_recommendation_inserts_new_row(in_memory_db):
    ok = db_operations.save_recommendation(
        user_id=42,
        job_id=1,
        course_id=1,  # we seeded course_id=1
        rating=4.8,
        explanation="Another great elective.",
        rank=2,
    )
    assert ok is True

    cursor = in_memory_db.cursor()
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM Recommendations WHERE user_id = ? AND job_id = ?;",
        (42, 1),
    )
    # Originally 1 row, now 2
    assert cursor.fetchone()["cnt"] == 2


def test_get_recommendations_returns_detailed_dicts(in_memory_db):
    recs = db_operations.get_recommendations(42, 1)
    assert len(recs) == 1

    rec = recs[0]
    assert rec["Course ID"] == 1
    assert rec["Course Code"] == "CPSC 120"
    assert rec["Course Name"] == "Introduction to Programming"
    assert rec["Units"] == 3
    assert rec["Rating"] == 4.5
    assert rec["Rank"] == 1
    assert "Recommended core elective" in rec["Explanation"]


# --- Simple ID lookups ---


def test_get_job_by_id_returns_row(in_memory_db):
    job = db_operations.get_job_by_id(1)
    assert job is not None
    assert job["job_id"] == 1
    assert job["name"] == "Software Engineer"


def test_get_degree_by_id_returns_row(in_memory_db):
    degree = db_operations.get_degree_by_id(1)
    assert degree is not None
    assert degree["degree_id"] == 1
    assert degree["name"] == "B.S. Computer Science"


def test_get_course_by_code_returns_row(in_memory_db):
    course = db_operations.get_course_by_code("CPSC 120")
    assert course is not None
    assert course["course_id"] == 1
    assert course["name"] == "Introduction to Programming"


def test_get_degree_electives_filters_by_subcategory(in_memory_db):
    # Only CPSC 120 has subcategory_id=5 (our "electives" flag)
    electives = db_operations.get_degree_electives(degree_id=1)
    assert len(electives) == 1
    assert electives[0]["course_id"] == 1
    assert electives[0]["course_code"] == "CPSC 120"
