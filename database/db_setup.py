import logging
import os
import sqlite3
from pathlib import Path  # Added Code

logger = logging.getLogger(__name__)  # Reuse the global logger


def create_connection(db_file):
    """Create a database connection to the SQLite database specified by db_file."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info(f"Connected to SQLite database: {db_file}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"SQLite connection error: {e}")
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
        logger.error(f"An error occurred while creating tables: {e}")
        conn.rollback()


def main_int_db(database: str = "smart_elective_advisor.db") -> None:
    logger.info("Starting database setup...")

    # Define the db directory path (at the current level)
    db_directory = os.path.join(os.getcwd(), "db")

    # Ensure the db directory exists, if not, create it
    if not os.path.exists(db_directory):
        os.makedirs(db_directory)
        logger.info(f"Created directory for database at {db_directory}")

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
                f"An error occurred during database setup at %s: %s", db_path, e
            )
            raise
        finally:
            # Close the connection
            conn.close()
            logger.info(f"Database setup completed. Database file: {db_path}")
    else:
        logger.error("Error! Cannot create the database connection.")
