# ui/app_version.py
"""
Helpers for locating and formatting the application's version text.
This module provides two internal helpers used by tests:
  - _load_version_json_text(): find and read version.json from the
    project root (current working directory) and return the raw path string.
  - _format_version_text(): format selected fields for display.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Tuple


def iso_zulu_to_json_parts(z: str) -> dict:
    """
    Very small, dependency-free ISO-8601 'Z' splitter.
    Returns {'date': 'YYYY-MM-DD', 'time': 'HH:MM:SSZ'} or raises.
    """
    if not isinstance(z, str) or "T" not in z:
        raise ValueError("invalid iso zulu")
    date_part, time_part = z.split("T", 1)
    # Keep trailing 'Z' if present (tests expect the 'Z' to remain).
    if not time_part:
        raise ValueError("invalid iso zulu")
    return {"date": date_part, "time": time_part}


def _format_version_text(payload_text: str) -> str:
    """
    Format a JSON string containing version metadata into human text.
    On invalid JSON, passthrough the original string (per tests).
    Expected fields: version, commit, date, datetime, defaultBranch.
    """
    try:
        data = json.loads(payload_text)
    except Exception:
        return payload_text

    lines = []

    version = data.get("version")
    if version:
        lines.append(f"version: {version}")

    commit = data.get("commit")
    if commit:
        lines.append(f"commit: {commit}")

    date_str = data.get("date")
    if date_str:
        lines.append(f"date: {date_str}")

    # Time line prefers parsed ISO 'datetime'; if parsing fails,
    # fall back to simple slicing so tests see '03:16:40Z'.
    dt = data.get("datetime")
    if dt:
        try:
            parts = iso_zulu_to_json_parts(dt)
            lines.append(f"Time: {parts['time']}")
        except Exception:
            # Fallback: keep substring after 'T' verbatim.
            try:
                lines.append(f"Time: {dt.split('T', 1)[1]}")
            except Exception:
                pass

    branch = data.get("defaultBranch")
    if branch:
        lines.append(f"Branch: {branch}")

    return "\n".join(lines)


def _load_version_json_text() -> Tuple[str, str]:
    """
    Look for version.json only in the project root (current working directory).
    Return (file_text, raw_candidate_string_that_matched).
    If it doesn't exist, raise FileNotFoundError.
    """
    cwd = Path.cwd()
    p = cwd / "version.json"
    if p.exists() and p.is_file():
        raw = os.path.join(".", "version.json")
        return p.read_text(encoding="utf-8"), raw
    raise FileNotFoundError("version.json not found in project root")


# Optional convenience wrappers your GUI could call (not required by tests).
def format_version_text_from_disk() -> str:
    """
    Load version.json via the search helper and format it for display.
    """
    text, _ = _load_version_json_text()
    return _format_version_text(text)
