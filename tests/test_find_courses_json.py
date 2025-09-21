# tests/test_find_courses_json.py
from pathlib import Path

from ai_integration.ai_module import _find_courses_json


def test_find_courses_json_prefers_cwd(tmp_path, monkeypatch):
    (tmp_path / "courses.json").write_text("[]", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert _find_courses_json() == tmp_path / "courses.json"
