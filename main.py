# main.py
import sys
from typing import Optional

from utilities.logger_setup import setup_logger

# logger = logging.getLogger(__name__)  # Reuse the global logger


def main() -> int:  # Changed Code
    """
    Entry point for the application.
    Returns an exit code (0 on success, non-zero on error).
    """
    # Configure logging first so loggers created below inherit handlers/formatters.
    setup_logger()  # Changed Code

    # Create module logger after logging is configured.
    import logging

    logger = logging.getLogger(__name__)

    # Load environment variables
    from utilities.load_env import load_environment

    try:
        load_environment()
    except ValueError as e:
        logger.error("Error loading environment: %s", e)
        # Exit with non-zero to indicate failure for CI/scripts.
        return 2

    # Initialize database
    from database.db_setup import main_int_db

    try:
        main_int_db()
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
        return 3

    # Initialize AI components
    from ai_integration.ai_module import main_int_ai

    try:
        main_int_ai()
    except Exception as e:
        logger.exception("AI initialization failed: %s", e)
        return 4

    # Start UI (blocking call)
    from ui.gui import main_int_ui

    try:
        main_int_ui()
    except Exception as e:
        logger.exception("UI initialization failed: %s", e)
        return 5

    logger.info("Program finished successfully.")
    return 0


if __name__ == "__main__":
    exit_code: int = main()
    # Use sys.exit to surface exit code to the shell.
    sys.exit(exit_code)
