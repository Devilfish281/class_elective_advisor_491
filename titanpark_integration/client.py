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
    base = get_titanpark_base_url()
    if not path.startswith("/"):
        path = "/" + path
    return base + path


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
    url = _build_url("/parking_data/all")
    timeout = get_titanpark_timeout()
    logger.info("Requesting TitanPark snapshot from %s (timeout=%s)", url, timeout)
    try:
        resp = requests.get(url, timeout=timeout)
    except Exception as exc:
        raise TitanParkError(f"Error contacting TitanPark at {url}: {exc}") from exc
    if not resp.ok:
        raise TitanParkError(
            f"TitanPark responded with HTTP {resp.status_code}: {resp.text!r}"
        )
    try:
        payload = resp.json()
    except Exception as exc:
        raise TitanParkError(f"Invalid JSON from TitanPark: {exc}") from exc

    # TitanPark returns a dict keyed by structure ID (e.g. "Nutwood_Structure").
    # Normalize that into a list of per-structure dicts that match our expectations.
    if isinstance(payload, dict):
        structures: List[Dict[str, Any]] = []
        for key, raw in payload.items():
            if not isinstance(raw, dict):
                logger.warning("Skipping non-dict structure %r: %r", key, raw)
                continue

            # Prefer the human-readable name from the payload, fall back to the key.
            name = raw.get("name") or raw.get("structure_name") or key.replace("_", " ")

            # TitanPark cheat sheet uses `total` / `available`; also accept legacy names.
            total_raw = raw.get("total_spots", raw.get("total"))
            available_raw = raw.get("available_spots", raw.get("available"))
            if total_raw is None or available_raw is None:
                logger.warning(
                    "Skipping structure %r with missing total/available: %r",
                    key,
                    raw,
                )
                continue
            try:
                total = int(total_raw)
                available = int(available_raw)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Skipping structure %r with invalid total/available: %s",
                    key,
                    exc,
                )
                continue

            if total < 0:
                total = 0
            if available < 0:
                available = 0
            if available > total:
                available = total

            occupied = max(total - available, 0)

            perc_full = raw.get("perc_full")
            occupancy_rate: float
            if perc_full is not None:
                try:
                    perc_full_f = float(perc_full)
                    # perc_full is a percentage [0,100]; convert to [0.0,1.0].
                    occupancy_rate = max(0.0, min(1.0, perc_full_f / 100.0))
                except (TypeError, ValueError):
                    occupancy_rate = (
                        float(occupied) / float(total or 1) if total > 0 else 1.0
                    )
            else:
                occupancy_rate = (
                    float(occupied) / float(total or 1) if total > 0 else 1.0
                )

            normalized: Dict[str, Any] = {
                "name": name,
                "structure_name": name,
                "total_spots": total,
                "available_spots": available,
                "occupied_spots": occupied,
                "occupancy_rate": occupancy_rate,
            }

            # Preserve pricing info if present so callers can use it.
            if "price_in_cents" in raw:
                normalized["price_in_cents"] = raw["price_in_cents"]

            structures.append(normalized)

        logger.debug(
            "Normalized TitanPark dict payload with %d structures", len(structures)
        )
        return structures

    # If the backend ever returns a list (old behavior), keep supporting it.
    if isinstance(payload, list):
        logger.debug(
            "Received list payload from TitanPark with %d structures", len(payload)
        )
        return payload

    raise TitanParkError(
        f"Expected dict or list of structures, got {type(payload).__name__}"
    )



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
    # Normalize to the ID-style name with underscores, as required by the API.
    struct_id = structure_name.strip().replace(" ", "_")
    encoded = quote(struct_id, safe="_")
    url = _build_url(f"/parking_data/{encoded}")
    timeout = get_titanpark_timeout()
    logger.info(
        "Requesting TitanPark structure %r (ID %r) from %s (timeout=%s)",
        structure_name,
        struct_id,
        url,
        timeout,
    )
    try:
        resp = requests.get(url, timeout=timeout)
    except Exception as exc:
        raise TitanParkError(f"Error contacting TitanPark at {url}: {exc}") from exc
    if not resp.ok:
        raise TitanParkError(
            f"TitanPark responded with HTTP {resp.status_code}: {resp.text!r}"
        )
    try:
        payload = resp.json()
    except Exception as exc:
        raise TitanParkError(f"Invalid JSON from TitanPark: {exc}") from exc
    if not isinstance(payload, dict):
        raise TitanParkError(
            f"Expected dict for structure, got {type(payload).__name__}"
        )
    logger.debug(
        "Received structure %r (ID %r) from TitanPark", structure_name, struct_id
    )
    return payload


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
    target = name.strip().lower()
    for struct in structures:
        raw_name = (
            struct.get("name") or struct.get("structure_name") or struct.get("id")
        )
        if not isinstance(raw_name, str):
            continue
        if raw_name.strip().lower() == target:
            return struct
    return None
