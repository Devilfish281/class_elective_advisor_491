#  titanpark_integration/config.py
"""Configuration helpers for TitanPark integration.

This module centralizes reading environment variables related to the
TitanPark backend so the rest of the codebase can stay clean and testable.

All functions are safe to call multiple times and only rely on
:mod:`os.environ`.
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_titanpark_base_url() -> str:
    """Return the TitanPark backend base URL.

    The value is taken from the :envvar:`TITANPARK_API_BASE_URL`
    environment variable if present; otherwise a conservative default
    of ``"http://127.0.0.1:8000"`` is used.

    :returns: Base URL (without trailing slash) used for TitanPark HTTP
              requests.
    :rtype: str
    """
    raw = os.getenv("TITANPARK_API_BASE_URL", "http://127.0.0.1:8000")
    url = raw.rstrip("/") or "http://127.0.0.1:8000"
    if raw != url:
        logger.debug("Normalizing TITANPARK_API_BASE_URL from %r to %r", raw, url)
    return url



def get_titanpark_timeout(default: float = 10.0) -> float:
    """Return the HTTP timeout used for TitanPark calls.

    Reads the :envvar:`TITANPARK_API_TIMEOUT` environment variable and
    attempts to parse it as a floating-point number of seconds. If parsing
    fails or the value is non-positive, *default* is returned instead.

    :param default: Fallback timeout in seconds when the environment
        variable is missing or invalid.
    :type default: float
    :returns: Timeout in seconds.
    :rtype: float
    """
    raw = os.getenv("TITANPARK_API_TIMEOUT")
    if raw is None:
        return float(default)
    try:
        value = float(raw)
        if value <= 0:
            raise ValueError("timeout must be positive")
        return value
    except Exception as exc:
        logger.warning(
            "Invalid TITANPARK_API_TIMEOUT=%r (%s); using default %s s",
            raw,
            exc,
            default,
        )
        return float(default)
