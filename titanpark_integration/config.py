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
    #  STUB: always return the default URL; students should read from the environment.
    return "http://127.0.0.1:8000"


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
    #  STUB: simply echo the default timeout; students should parse the env var.
    return float(default)
