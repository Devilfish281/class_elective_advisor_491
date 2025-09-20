import os

from database import db_setup

def test_main_test_db_option_2_in_memory():
    """
    Option 2: in-memory schema creation.

    This calls the code path that creates a ':memory:' sqlite connection and
    runs create_tables(conn). We assert True to indicate the module's test
    dispatcher returned success. Note:

      - ':memory:' databases are tied to a single connection; separate
        connections using ':memory:' are independent unless you use
        shared-cache/URI forms. If your code uses multiple connections and
        expects shared state, prefer a file-backed DB for integration tests.
    """
    assert db_setup.main_test_db(2) is True


def test_main_test_db_option_3_tempfile(tmp_path):
    """
    Option 3: tempfile smoke test.

    The module creates a temporary sqlite file internally, writes a simple
    record, reads it back and removes the file. We assert the call returns True.

    If you want to assert the file was created at a specific path or exercise
    the lower-level helpers with a path you control, see the example below.
    """
    assert db_setup.main_test_db(3) is True
