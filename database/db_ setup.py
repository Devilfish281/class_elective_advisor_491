#db_setup.py
import logging
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)  # Reuse the global logger


def create_connection(db_file) -> Optional["sqlite3.Connection"]:
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info("Connected to SQLite database: %s", db_file)
        return conn
    except sqlite3.Error as e:
        logger.error("SQLite connection error: %s", e)
    return conn


def create_tables(conn):
    """Create tables in the SQLite database."""
    try:
        cursor = conn.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Create Colleges Table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS metadata (
            k TEXT PRIMARY KEY,
              v TEXT);
              """
        )

        conn.commit()
        logger.info("All tables created successfully.")

    except sqlite3.Error as e:
        logger.error("An error occurred while creating tables: %s", e)
        conn.rollback()


def main_int_db(database: str = "smart_elective_advisor.db") -> None:
    logger.info("Starting database setup...")

    # Define the db directory path (at the current level)
    db_directory = os.path.join(os.getcwd(), "db")

    # Ensure the db directory exists, if not, create it
    if not os.path.exists(db_directory):
        os.makedirs(db_directory, exist_ok=True)
        logger.info("Created directory for database at %s", db_directory)

    # Define the database path inside the db directory
    db_path = os.path.join(db_directory, database)

    # Create a database connection
    conn = create_connection(db_path)

    if conn is not None:
        try:
            # Create tables
            create_tables(conn)
        except Exception as e:
            logger.error(
                "An error occurred during database setup at %s: %s", db_path, e
            )
            raise
        finally:
            # Close the connection
            conn.close()
            logger.info("Database setup completed. Database file: %s", db_path)
    else:
        logger.error("Error! Cannot create the database connection.")


def main_test_db(option: int) -> bool:
    """
    DB test dispatcher:
      option 1 -> call main_int_db(database="cli_test_db_option1.sqlite") (creates file under ./db)
      option 2 -> in-memory schema test (calls create_tables on ':memory:')
      option 3 -> tempfile smoke test (creates a temp sqlite file, runs simple insert/select)
    Returns True on success, False on failure.
    """
    logger.info("main_test_db: selected option %s", option)

    if option == 1:
        try:
            # Calls the real initializer and writes ./db/smart_elective_advisor.db
            main_int_db(database="smart_elective_advisor.db")
            logger.info("main_test_db option 1: main_int_db completed successfully.")
            return True
        except Exception:
            logger.exception("main_test_db option 1 failed")
            return False

    elif option == 2:
        conn = None
        try:
            conn = create_connection(":memory:")
            if conn is None:
                logger.error(
                    "main_test_db option 2: failed to create in-memory connection"
                )
                return False
            create_tables(conn)
            logger.info("main_test_db option 2: in-memory create_tables OK")
            return True
        except Exception:
            logger.exception("main_test_db option 2 failed")
            return False
        finally:
            if conn:
                conn.close()

    elif option == 3:
        try:
            # Use a temporary file to avoid polluting repo. This file will be deleted automatically.
            fd, tmp_path = tempfile.mkstemp(suffix=".sqlite")
            os.close(fd)
            logger.info("main_test_db option 3: temp DB at %s", tmp_path)
            conn = create_connection(tmp_path)
            if conn is None:
                logger.error(
                    "main_test_db option 3: failed to create temp DB connection"
                )
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                return False
            # simple smoke test: create tables, insert/select
            create_tables(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO metadata (k, v) VALUES (?, ?)", ("t", "1")
            )
            conn.commit()
            cursor.execute("SELECT v FROM metadata WHERE k = ?", ("t",))
            r = cursor.fetchone()
            conn.close()
            os.remove(tmp_path)
            ok = r is not None and r[0] == "1"
            if ok:
                logger.info("main_test_db option 3: tempfile smoke test passed")
            else:
                logger.error(
                    "main_test_db option 3: tempfile smoke test failed (unexpected result)"
                )
            return ok
        except Exception:
            logger.exception("main_test_db option 3 failed")
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return False

    else:
        logger.error("main_test_db: unknown option %s", option)
        return False
