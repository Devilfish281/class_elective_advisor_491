# tests/test_ai_fake_errors.py
import json

# tests/test_ai_fake_errors.py
import pytest

import ai_integration.ai_module as ai


def test_fake_chatgpt_missing_file(monkeypatch, tmp_path):
    # Force the resolver to point at a *nonexistent* courses.json under tmp_path.
    monkeypatch.setattr(ai, "_find_courses_json", lambda: tmp_path / "courses.json")
    # Make sure "AI off" so we go through fake loader.
    monkeypatch.delenv("AI_ENABLED", raising=False)

    with pytest.raises(FileNotFoundError):
        ai.fake_chatgpt_response(1, "Web Dev", "BSc", [])


def test_fake_chatgpt_bad_json(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_ENABLED", raising=False)
    (tmp_path / "courses.json").write_text(
        '{"not":"a list"', encoding="utf-8"
    )  # malformed
    monkeypatch.chdir(tmp_path)
    with pytest.raises(json.JSONDecodeError):
        ai.fake_chatgpt_response(1, "Web Dev", "BSc", [])
