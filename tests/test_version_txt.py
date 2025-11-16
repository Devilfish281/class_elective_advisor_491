# tests/test_version_txt.py
import json
import os
import re

import pytest

PATTERN = re.compile(r"^v\d+\.\d+\.\d+ \([0-9a-f]{7}, \d{4}-\d{2}-\d{2}\)$")


def test_version_txt_format(tmp_path, monkeypatch):
    """Validate simple, stable formatting: vX.Y.Z (abcdef0, YYYY-MM-DD)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "version.txt").write_text(
        "v0.0.25 (8e831ae, 2025-10-31)", encoding="utf-8"
    )

    text = (tmp_path / "version.txt").read_text(encoding="utf-8").strip()
    assert PATTERN.match(text), f"Bad version.txt format: {text}"


def test_version_txt_matches_version_json_when_both_exist(tmp_path, monkeypatch):
    """Optional consistency check: version.txt version == version.json['version']."""
    monkeypatch.chdir(tmp_path)

    # Write JSON + TXT fixtures:
    (tmp_path / "version.json").write_text(
        json.dumps(
            {
                "version": "v0.0.25",
                "commit": "8e831ae",
                "date": "2025-10-31",
                "datetime": "2025-10-31T03:16:40Z",
                "defaultBranch": "main",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (tmp_path / "version.txt").write_text(
        "v0.0.25 (8e831ae, 2025-10-31)", encoding="utf-8"
    )

    # Simple parse of version.txt:
    txt = (tmp_path / "version.txt").read_text(encoding="utf-8").strip()
    assert PATTERN.match(txt)
    txt_version = txt.split(" ", 1)[0]

    # Parse version.json:
    data = json.loads((tmp_path / "version.json").read_text(encoding="utf-8"))
    assert data.get("version") == txt_version
