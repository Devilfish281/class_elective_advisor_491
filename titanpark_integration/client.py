# titanpark_integration/clinet.py
"""HTTP client for the TitanPark parking-system backend.

This module wraps the TitanPark FastAPI endpoints in a small,
synchronous client that can be called from the Smart Elective Advisor
desktop application.

Only a subset of endpoints is modeled here:

* ``GET /parking_data/all`` - snapshot of all parking structures.
* ``GET /parking_data/{structure_name}`` - details for a single structure.

The exact JSON shape of each structure depends on the TitanPark
implementation. Per the API cheat sheet, each structure provides:

* ``structure_name``: human-readable name
* ``total_spots``: total number of spaces
* ``available_spots``: currently free spaces
* ``occupied_spots``: currently occupied spaces
* ``occupancy_rate``: fraction of occupied spaces
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

import requests

from .config import get_titanpark_base_url, get_titanpark_timeout

logger = logging.getLogger(__name__)


class TitanParkError(RuntimeError):
    """Generic error raised for TitanPark HTTP or parsing failures."""


def _build_url(path: str) -> str:
    """Join the base URL with a relative *path*.

    :param path: Relative path such as ``"/parking_data/all"``.
    :type path: str
    :returns: Absolute URL to be used with :mod:`requests`.
    :rtype: str
    """
    # TODO: Build a real URL from the base URL and path.
    return "http://127.0.0.1:8000/dummy"


def fetch_parking_snapshot() -> List[Dict[str, Any]]:
    """Fetch a snapshot of all parking structures.

    This function issues a ``GET /parking_data/all`` request to the
    TitanPark backend and returns the decoded JSON payload.

    Per the cheat sheet, each structure is expected to contain:

    * ``structure_name`` (string)
    * ``total_spots`` (int)
    * ``available_spots`` (int)
    * ``occupied_spots`` (int)
    * ``occupancy_rate`` (float)

    :returns: List of dictionaries, one per structure, as returned by the
              backend.
    :rtype: list[dict[str, Any]]
    :raises TitanParkError: On network error, non-2xx status code, or
        invalid JSON response.
    """
    #  STUB: return a dummy list; students should implement the real HTTP call.
    return [
        {
            "name": "Dummy Structure",
            "structure_name": "Dummy Structure",
            "total_spots": 0,
            "available_spots": 0,
            "occupied_spots": 0,
            "occupancy_rate": 0.0,
        }
    ]


def fetch_structure_details(structure_name: str) -> Dict[str, Any]:
    """Fetch a single structure's details via ``GET /parking_data/{structure_name}``.

    The TitanPark backend expects the *underscore-style* structure ID in
    the path (for example ``"Nutwood_Structure"``), but this function
    also accepts human-readable names like ``"Nutwood Structure"`` and
    converts spaces to underscores before calling the API.

    :param structure_name: Structure identifier, such as
        ``"Nutwood_Structure"`` or ``"Nutwood Structure"``.
    :type structure_name: str
    :returns: Raw JSON dictionary for the structure.
    :rtype: dict[str, Any]
    :raises TitanParkError: On network error, non-2xx status code, or invalid JSON.
    """
    #  STUB: return a dummy structure; students should call the real endpoint.
    return {
        "structure_name": structure_name,
        "total_spots": 0,
        "available_spots": 0,
        "occupied_spots": 0,
        "occupancy_rate": 0.0,
    }


def find_structure_snapshot(
    structures: Iterable[Dict[str, Any]], name: str
) -> Optional[Dict[str, Any]]:
    """Find a single structure dictionary by *name*.

    Matching is case-insensitive and trims leading/trailing whitespace.

    :param structures: Iterable of raw structure dictionaries returned
        by :func:`fetch_parking_snapshot`.
    :type structures: iterable[dict[str, Any]]
    :param name: Human-readable structure name (for example
        ``"Nutwood Structure"``).
    :type name: str
    :returns: Matching structure dictionary, or ``None`` if not found.
    :rtype: dict[str, Any] | None
    """
    #  STUB: students should search through *structures* for the matching name.
    return None
