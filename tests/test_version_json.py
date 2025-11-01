# tests/test_version_json.py
import json
import os
import re
from pathlib import Path

import pytest

from ui import app_version as av


def _write_version_json_at(path: Path):
    path.write_text(
        json.dumps(
            {
                "version": "v0.0.25",
                "commit": "8e831ae",
                "date": "2025-10-31",
                "datetime": "2025-10-31T03:16:40Z",
                "defaultBranch": "main",
            }
        ),
        encoding="utf-8",
    )


def test__load_version_json_text_root_only(tmp_path, monkeypatch):
    """Root-only: find version.json in CWD and return raw './version.json' (Windows '.\\version.json')."""
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "version.json"
    _write_version_json_at(target)

    text, found_path = av._load_version_json_text()

    # Regex requirement: 'v' + digits '.' digits '.' digits
    assert re.match(r"^v\d+\.\d+\.\d+$", json.loads(text)["version"])

    # Path requirement: endswith of normalized('.'/'version.json')
    rhs = os.path.normpath(os.path.join(".", "version.json"))
    assert os.path.normpath(found_path).endswith(rhs)


def test__load_version_json_text_raises_when_missing(tmp_path, monkeypatch):
    """Root-only: must raise when root version.json is absent."""
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "version.json"
    if p.exists():
        p.unlink()
    with pytest.raises(FileNotFoundError):
        av._load_version_json_text()


def test__format_version_text_happy_path():
    """Keep existing formatter coverage intact."""
    payload = {
        "version": "v1.2.3",
        "commit": "abc1234",
        "date": "2025-10-31",
        "datetime": "2025-10-31T03:16:40Z",
        "defaultBranch": "main",
    }
    out = av._format_version_text(json.dumps(payload))
    lines = out.splitlines()
    assert lines[0] == "version: v1.2.3"
    assert "commit: abc1234" in lines
    assert "date: 2025-10-31" in lines
    assert "Time: 03:16:40Z" in lines
    assert "Branch: main" in lines


def test__format_version_text_passthrough_on_bad_json():
    """Existing behavior: on non-JSON, return input unmodified."""
    out = av._format_version_text("{not-json")
    assert out == "{not-json"
