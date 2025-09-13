# tests/test_load_env.py
"""
Tests for utilities.load_env.load_environment().

Two behaviors are tested:
  1) When no API key is present (and no .env is found), load_environment() should raise ValueError.
  2) When a valid-looking API key is present, load_environment() should succeed (not raise).
"""

import pytest

from utilities import load_env


def test_load_environment_missing(monkeypatch):
    """
    Simulate "no .env file found" and "no OPENAI_API_KEY in environment".
    We patch load_env.find_dotenv to return an empty string so that the module's
    load_dotenv() call will not load any file, and delete OPENAI_API_KEY from env.
    """
    # Make the module act as if there is no .env file to be found.
    monkeypatch.setattr(load_env, "find_dotenv", lambda: "")

    # Ensure the environment variable is not present for this test.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Expect ValueError because load_environment should validate and reject missing/invalid key.
    with pytest.raises(ValueError):
        load_env.load_environment()


def test_load_environment_valid(tmp_path, monkeypatch):
    """
    Verify load_environment() succeeds when a valid-looking API key is available.
    Two options shown below — this test uses a direct environment set (fast).
    If you want to test file-based loading specifically, patch find_dotenv to return
    the path of the temp .env file instead of setting the env var directly.
    """
    # Option A: create a .env file and instruct the loader to use it (uncomment to use)
    # env_file = tmp_path / ".env"
    # env_file.write_text("OPENAI_API_KEY=sk_test_" + "A" * 40)
    # monkeypatch.setattr(load_env, "find_dotenv", lambda: str(env_file))

    # Option B (used here): simply set a valid-looking API key in the environment.
    monkeypatch.setenv("OPENAI_API_KEY", "sk_test_" + "A" * 40)

    # If load_environment raises, the test fails; success = no exception.
    load_env.load_environment()
