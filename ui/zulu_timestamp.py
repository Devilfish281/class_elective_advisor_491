# ui/zulu_timestamp.py

from datetime import datetime


def iso_zulu_to_json_parts(ts: str) -> dict:
    """
    Parse an ISO-8601 UTC ('Z') timestamp like 'YYYY-MM-DDTHH:MM:SSZ'
    and return a dict of each component using only the Python stdlib.
    """
    # Normalize 'Z' to explicit zero offset for fromisoformat()
    # (3.11+ can parse 'Z', but this keeps behavior explicit & portable)
    norm = ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(norm)

    year = f"{dt.year:04d}"
    month = f"{dt.month:02d}"
    day = f"{dt.day:02d}"
    hour = f"{dt.hour:02d}"
    minute = f"{dt.minute:02d}"
    second = f"{dt.second:02d}"

    # Compute "+HH:MM" or "-HH:MM" from tzinfo
    offset = dt.utcoffset()
    if offset is None:
        utc_offset = "+00:00"
    else:
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        total_minutes = abs(total_minutes)
        utc_offset = f"{sign}{total_minutes // 60:02d}:{total_minutes % 60:02d}"

    return {
        "original": ts,
        "date": f"{year}-{month}-{day}",
        "year": year,
        "month": month,
        "day": day,
        "iso8601_separator": "T",
        "time_UTC": f"{hour}:{minute}:{second}",
        "hour": hour,
        "minute": minute,
        "second": second,
        "timezone_designator": "Z" if ts.endswith("Z") else "",
        "utc_offset": utc_offset,
    }
