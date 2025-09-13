# tests/conftest.py
"""
Project-wide pytest fixtures for the test suite.

This file is automatically discovered by pytest; fixtures defined here are available
to any test in the same directory tree without explicit imports. Use this file for
shared test setup/teardown utilities (env isolation, temporary paths, reusable
test data, etc.). See pytest docs for `conftest.py` and fixtures.
"""

import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """
    Automatically run for every test to provide environment isolation.

    Purpose:
      - Remove or normalize environment variables (for example OPENAI_API_KEY)
        so tests are deterministic and don't pick up values from the developer
        machine or CI runner.

    Behavior:
      - Runs before each test (function-scope by default).
      - Uses pytest's `monkeypatch` fixture to delete/set env vars; monkeypatch
        automatically restores changes after the test ends.
      - `raising=False` means deletion is silent if the var is already absent.
    """
    # Ensure OPENAI_API_KEY is not present by default for tests that expect "no key".
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # If you needed setup values, you could monkeypatch.setenv(...) here.
    yield
    # Teardown after yield isn't required because monkeypatch undoes env changes,
    # but you could add explicit cleanup after the yield if needed.


@pytest.fixture
def valid_api_key(monkeypatch):
    """
    Provide a safe, valid-looking OPENAI_API_KEY for tests that require a key.

    Usage:
        def test_something(valid_api_key):
            # valid_api_key is already set in the environment for this test
            assert os.getenv("OPENAI_API_KEY") == valid_api_key

    This uses monkeypatch.setenv so the environment is restored after the test.
    """
    key = "sk_test_" + "A" * 40
    monkeypatch.setenv("OPENAI_API_KEY", key)
    return key


@pytest.fixture
def temp_db_path(tmp_path):
    """
    Return a temporary sqlite database path (string) for use in tests.

    tmp_path is a pytest built-in fixture that provides a pathlib.Path to a fresh
    temporary directory unique to the test invocation; using it avoids polluting
    the repo and ensures isolation between tests.
    """
    p = tmp_path / "test_db.sqlite"
    return str(p)
