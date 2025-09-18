# tests/test_ai_module.py  # Added Code
"""Unit tests for ai_integration.ai_module."""  # Added Code

import inspect  # Added Code
import os  # Added Code
from importlib import util as importlib_util  # Added Code

import pytest  # Added Code

# Import the module under test  # Added Code
import ai_integration.ai_module as ai  # Added Code


# ----------------------------- main_int_ai -----------------------------  # Added Code
def test_main_int_ai_returns_false_without_key():  # Added Code
    """isolate_env (autouse) removes OPENAI_API_KEY, so init should be False."""  # Added Code
    assert ai.main_int_ai() is False  # Added Code


def test_main_int_ai_returns_true_with_key(valid_api_key):  # Added Code
    """With a valid key set by the fixture, init should be True."""  # Added Code
    assert ai.main_int_ai() is True  # Added Code


# ----------------------------- main_test_ai (option 1) -----------------------------  # Added Code
def test_main_test_ai_option1_tracks_main_int_ai_without_key():  # Added Code
    """Option 1 proxies to main_int_ai; without key it should be False."""  # Added Code
    assert ai.main_test_ai(1) is False  # Added Code


def test_main_test_ai_option1_tracks_main_int_ai_with_key(valid_api_key):  # Added Code
    """Option 1 proxies to main_int_ai; with key it should be True."""  # Added Code
    assert ai.main_test_ai(1) is True  # Added Code


# ----------------------------- main_test_ai (option 2) -----------------------------  # Added Code
def test_main_test_ai_option2_returns_false_without_key():  # Added Code
    """Option 2: should warn/False when key is absent."""  # Added Code
    assert ai.main_test_ai(2) is False  # Added Code


def test_main_test_ai_option2_returns_true_with_key(valid_api_key):  # Added Code
    """Option 2: should True when key present (and log masked prefix)."""  # Added Code
    assert ai.main_test_ai(2) is True  # Added Code


# ----------------------------- main_test_ai (option 3) -----------------------------  # Added Code
def test_main_test_ai_option3_returns_false_when_openai_missing(
    monkeypatch,
):  # Added Code
    """Force find_spec('openai') -> None so option 3 returns False."""  # Added Code
    monkeypatch.setattr(
        ai.importlib.util, "find_spec", lambda name: None, raising=True
    )  # Added Code
    assert ai.main_test_ai(3) is False  # Added Code


def test_main_test_ai_option3_returns_true_when_openai_present(
    monkeypatch,
):  # Added Code
    """Force find_spec('openai') -> a dummy spec-like object so option 3 returns True."""  # Added Code
    monkeypatch.setattr(
        ai.importlib.util, "find_spec", lambda name: object(), raising=True
    )  # Added Code
    assert ai.main_test_ai(3) is True  # Added Code


# ----------------------------- main_test_ai (unknown option) -----------------------------  # Added Code
def test_main_test_ai_unknown_option_returns_false():  # Added Code
    """Unknown option path should return False."""  # Added Code
    assert ai.main_test_ai(999) is False  # Added Code
