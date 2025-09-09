# main.py
"""Smart Elective Advisor - CLI entrypoint and test runners.

This module provides CLI entrypoints to run individual subsystem tests (AI, DB, UI)
or to start the full application. The functions in this module are documented with
Sphinx/reStructuredText field lists so Sphinx autodoc (and napoleon) will render
the function signatures and parameter/return documentation cleanly.

Usage examples (from project root):
    poetry run python main.py -ai 1
    poetry run python main.py -db 2
    poetry run python main.py -ui 3
    poetry run python main.py -ai 1 -db 3 -ui 2

Notes:
- For Sphinx, enable `sphinx.ext.autodoc` and optionally `sphinx.ext.napoleon` to
  accept Google / NumPy-style docstrings. The docstrings here use classic reST
  field lists so they work with autodoc out of the box.  # Added Code
"""
import argparse
import logging
import sys
from typing import Optional

from utilities.logger_setup import setup_logger

# logger = logging.getLogger(__name__)  # Reuse the global logger

# --------------------------
# Exit-code descriptions
# --------------------------
_EXIT_DESCRIPTIONS = {  # Added Code
    "setup": {  # Added Code
        0: "Environment loaded: OK.",  # Added Code
        2: "Environment load failed (e.g., OPENAI_API_KEY missing/invalid).",  # Added Code
    },  # Added Code
    "ai_test": {  # Added Code
        0: "AI test passed.",  # Added Code
        1: "AI test failed.",  # Added Code
        2: "AI test raised an exception.",  # Added Code
    },  # Added Code
    "db_test": {  # Added Code
        0: "DB test passed.",  # Added Code
        1: "DB test failed.",  # Added Code
        2: "DB test raised an exception.",  # Added Code
    },  # Added Code
    "ui_test": {  # Added Code
        0: "UI test passed.",  # Added Code
        1: "UI test failed or raised an exception.",  # Added Code
    },  # Added Code
    "main": {  # Added Code
        0: "Program finished successfully.",  # Added Code
        3: "Database initialization failed.",  # Added Code
        4: "AI initialization failed.",  # Added Code
        5: "UI initialization failed.",  # Added Code
        130: "Interrupted by user (KeyboardInterrupt/SIGINT).",  # Added Code
    },  # Added Code
    "tests": {  # Added Code
        0: "All requested tests passed.",  # Added Code
        1: "At least one test failed.",  # Added Code
        2: "At least one test raised an exception.",  # Added Code
    },  # Added Code
}  # Added Code


def describe_exit_code(context: str, code: int) -> str:  # Added Code
    """Return a human-readable description for a given exit code in a context."""  # Added Code
    return _EXIT_DESCRIPTIONS.get(context, {}).get(
        code, f"Unknown exit code {code}."
    )  # Added Code


def report_exit_code(context: str, code: int) -> None:  # Added Code
    """Log and print a description of the exit code for the given context."""  # Added Code
    msg = describe_exit_code(context, code)  # Added Code
    logging.getLogger(__name__).info(
        "[%s] %s (code=%s)", context, msg, code
    )  # Added Code
    print(f"[{context}] {msg} (code={code})")  # Added Code


def _run_ai_test(option: int) -> int:
    """Run an AI subsystem test and return a process-style exit code.

    This wrapper imports and calls :func:`ai_integration.ai_module.main_test_ai`
    passing the received option integer through.

    :param option: integer selecting the AI test variant (1..3)
    :type option: int
    :returns: 0 on success, 1 on test-level failure, 2 on unexpected exception
    :rtype: int
    :raises ImportError: if the AI test module cannot be imported
    """
    logger = logging.getLogger(__name__)
    try:
        from ai_integration.ai_module import main_test_ai

        logger.info("Running AI test...")
        ok = main_test_ai(option)
        if ok:
            logger.info("AI test passed.")
            return 0
        logger.error("AI test failed.")
        return 1
    except Exception:
        logger.exception("Exception while running AI test")
        return 2


def _run_db_test(option: int) -> int:
    """Run a DB subsystem test and return a process-style exit code.

    This wrapper imports and calls :func:`database.db_setup.main_test_db`
    passing the received option integer through.

    :param option: integer selecting the DB test variant (1..3)
    :type option: int
    :returns: 0 on success, 1 on test-level failure, 2 on unexpected exception
    :rtype: int
    :raises ImportError: if the database module cannot be imported
    """
    logger = logging.getLogger(__name__)
    try:
        from database.db_setup import main_test_db

        logger.info("Running DB test...")
        ok = main_test_db(option)
        if ok:
            logger.info("DB test passed.")
            return 0
        logger.error("DB test failed.")
        return 1
    except Exception:
        logger.exception("Exception while running DB test")
        return 2


def _run_ui_test(option: int) -> int:
    """Run a UI subsystem test and return a process-style exit code.

    This wrapper imports and calls :func:`ui.gui.main_test_ui` which provides
    several UI test variants (for example: launch-and-block, create/destroy,
    auto-close for CI). Use the integer `option` to pick the variant.

    :param option: integer selecting the UI test variant (1..3)
    :type option: int
    :returns: 0 on success, 1 on failure or exception
    :rtype: int
    :raises ImportError: if the UI module cannot be imported
    """
    logger = logging.getLogger(__name__)
    try:
        from ui.gui import main_int_ui

        logger.info("Launching UI (test mode)...")
        ok = main_int_ui(option)
        if ok:
            logger.info("UI test passed.")
            return 0
        logger.error("UI test failed.")
        return 1

    except Exception:
        logger.exception("Exception while running UI")
        return 1


def main_setup() -> int:
    """Set up logging and environment for the application.

    This function configures the project logger by calling :func:`setup_logger`
    and then attempts to load and validate environment variables using
    :func:`utilities.load_env.load_environment`.

    :returns: 0 on success, 2 if environment loading failed
    :rtype: int
    :raises ValueError: when environment variables are missing or invalid
    """

    # Configure logging first so loggers created below inherit handlers/formatters.
    setup_logger()

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

    # Success - explicitly return 0
    return 0


def main() -> int:
    """Run the full application (database init → AI init → UI).

    The function performs the high-level startup sequence:
    1. Initialize database via :func:`database.db_setup.main_int_db`
    2. Initialize AI via :func:`ai_integration.ai_module.main_int_ai`
    3. Start the UI via :func:`ui.gui.main_int_ui` (blocking call)

    Exit codes:
      * 0 — success (program finished)
      * 3 — database initialization failed
      * 4 — AI initialization failed
      * 5 — UI initialization failed

    :returns: exit code suitable for `sys.exit()`
    :rtype: int
    :raises Exception: any unexpected exception will be logged and results in non-zero exit
    """
    logger = logging.getLogger(__name__)

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
    # ensure all logging handlers flush to file before exit
    import logging

    logging.shutdown()
    return 0


if __name__ == "__main__":
    exit_code = 0

    # Run setup of environment and logging first so tests produce logs
    exit_code: int = main_setup()
    report_exit_code("setup", exit_code)
    if exit_code != 0:
        sys.exit(exit_code)

    """
    DEBUGGING / TESTING USAGE:
    poetry run python run_debug.py -ai 1

    poetry run python main.py -ai 1
    poetry run python main.py -db 2
    poetry run python main.py -ui 3

    poetry run python main.py -ai 1 -db 3 -ui 2

    """

    # Parse CLI flags to allow running section tests independently and then exit.
    parser = argparse.ArgumentParser(
        description="Smart Elective Advisor CLI"
    )  # Added Code
    parser.add_argument(
        "-db",
        type=int,
        choices=[1, 2, 3],
        help="Run DB test variant (1..3) and pass the number to _run_db_test()",  # Added Code
    )
    parser.add_argument(
        "-ai",
        type=int,
        choices=[1, 2, 3],
        help="Run AI test variant (1..3) and pass the number to _run_ai_test()",  # Added Code
    )
    parser.add_argument(
        "-ui",
        type=int,
        choices=[1, 2, 3],
        help="Run UI test variant (1..3) and pass the number to _run_ui_test()",  # Added Code
    )
    args = parser.parse_args()

    if args.ai or args.db or args.ui:
        # run requested tests in order: ai -> db -> ui. Exit after running.
        exit_code = 0
        if args.ai:
            rc = _run_ai_test(args.ai)
            report_exit_code("ai_test", rc)
            exit_code = exit_code or rc
        if args.db:
            rc = _run_db_test(args.db)
            report_exit_code("db_test", rc)
            exit_code = exit_code or rc
        if args.ui:
            rc = _run_ui_test(args.ui)
            report_exit_code("ui_test", rc)
            exit_code = exit_code or rc

        # Summarize the overall tests outcome using the final exit_code
        summary_ctx = "tests"
        report_exit_code(summary_ctx, 0 if exit_code == 0 else exit_code)
        sys.exit(exit_code)

    try:
        exit_code: int = main()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Interrupted by user (KeyboardInterrupt).")
        exit_code = 130

    report_exit_code("main", exit_code)
    sys.exit(exit_code)
