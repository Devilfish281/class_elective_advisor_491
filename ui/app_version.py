# ui/app_version.py
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

# import the Zulu parser
try:
    from ui.zulu_timestamp import iso_zulu_to_json_parts
except Exception:
    from .zulu_timestamp import iso_zulu_to_json_parts


def _load_version_json_text() -> tuple[str, str]:
    """Load contents of version.json from common locations. Returns (text, path)."""
    candidates = [
        "version.json",
        os.path.join("config", "version.json"),
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "version.json")),
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read(), p
    raise FileNotFoundError(
        f"version.json not found. Looked in: {', '.join(map(os.path.normpath, candidates))}"
    )


def _format_version_text(raw_text: str) -> str:
    """Return human-readable text with `version` first, no braces, and key renames."""
    try:
        data = json.loads(raw_text)
    except Exception:
        return raw_text.strip()
    lines = []
    if "version" in data:
        lines.append(f'version: {data.get("version")}')
    if "commit" in data:
        lines.append(f'commit: {data.get("commit")}')
    if "date" in data:
        lines.append(f'date: {data.get("date")}')

    # --- Only show time; keep 'Z' at the end if present ---
    if "datetime" in data:
        ts = str(data.get("datetime"))
        time_str = None
        keep_z = ts.endswith("Z")

        # Preferred path: parse with your helper (handles Z and offsets)
        try:
            parts = iso_zulu_to_json_parts(ts)
            time_str = parts.get("time_UTC")
        except Exception:
            # Fallback: slice between 'T' and zone part (Z / +HH:MM / -HH:MM)
            if "T" in ts:
                after_t = ts.split("T", 1)[1]
                time_str = after_t.split("Z")[0].split("+")[0].split("-")[0].strip()

        if time_str:
            if keep_z:
                lines.append(f"Time: {time_str}Z")
            else:
                lines.append(f"Time: {time_str}")
        else:
            # Ultimate fallback: keep original field if parsing fails
            lines.append(f"datetime: {ts}")
    # --- end change ---

    # if "datetime" in data:
    #     lines.append(f'datetime: {data.get("datetime")}')

    branch_value = data.get("defaultBranch")
    if branch_value is not None:
        lines.append(f"Branch: {branch_value}")
    handled = {"version", "commit", "date", "datetime", "defaultBranch"}
    for k, v in data.items():
        if k not in handled:
            lines.append(f"{k}: {v}")

    # OPTIONAL: if there's a UTC 'Z' timestamp, append a parsed breakdown using our helper
    ts = data.get("datetime")
    if (
        isinstance(ts, str)
        and ("T" in ts)
        and (ts.endswith("Z") or "+" in ts or "-" in ts)
    ):
        try:
            parts = iso_zulu_to_json_parts(ts)  # <-- call into zulu_timestamp.py
            zulu_printed = False
            if zulu_printed is True and parts.get("timezone_designator") == "Z":
                lines.append("")  # spacer
                lines.append("Parsed UTC timestamp:")
                # Present in a friendly, stable order
                for key in (
                    "original",
                    "date",
                    "year",
                    "month",
                    "day",
                    "iso8601_separator",
                    "time_UTC",
                    "hour",
                    "minute",
                    "second",
                    "timezone_designator",
                    "utc_offset",
                ):
                    if key in parts:
                        lines.append(f"  {key}: {parts[key]}")
        except Exception as _e:
            # Non-fatal; just skip the breakdown if parsing fails
            pass

    return "\n".join(lines)


def show_about_dialog(parent_widget: tk.Widget) -> None:
    """Open a modal dialog showing human-friendly version information (no braces)."""
    try:
        raw_text, _ = _load_version_json_text()
        friendly = _format_version_text(raw_text)
        display_text = "Smart Elective Advisor\nVersion Information\n\n" + friendly
    except Exception as e:
        messagebox.showerror(
            "About - Version Info", f"Couldn't load version info:\n{e}"
        )
        return

    # Build modal dialog
    top = tk.Toplevel(parent_widget)
    top.title("About - Version Info")
    top.geometry("650x420")

    text_widget = tk.Text(top, wrap="word", font=("Consolas", 11))
    yscroll = ttk.Scrollbar(top, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=yscroll.set)
    text_widget.insert("1.0", display_text)
    text_widget.config(state="disabled")
    text_widget.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
    yscroll.pack(side="right", fill="y", padx=(0, 10), pady=10)

    btn_row = ttk.Frame(top)
    btn_row.pack(fill="x", padx=10, pady=(0, 10))
    ttk.Button(btn_row, text="Close", command=top.destroy).pack(side="right")

    # Make it behave as a proper modal child of the parent
    top.transient(parent_widget.winfo_toplevel())
    top.grab_set()
    top.focus()
