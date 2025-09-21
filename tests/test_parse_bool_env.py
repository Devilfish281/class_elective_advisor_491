# tests/test_parse_bool_env.py
import os

from ai_integration.ai_module import parse_bool_env


def test_parse_bool_truthy(monkeypatch):
    for v in ["1", "true", "yes", "y", "on", "t", "TRUE", "On", "  yes  "]:
        monkeypatch.setenv("X", v)
        assert parse_bool_env("X", default=False) is True


def test_parse_bool_default(monkeypatch):
    monkeypatch.delenv("X", raising=False)
    assert parse_bool_env("X", default=True) is True
    assert parse_bool_env("X", default=False) is False
