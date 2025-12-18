#  titanpark_integration/recommendation.py
"""Parking recommendation logic built on top of the TitanPark client.

The goal of this module is to provide a single high-level function:

* :func:`recommend_parking_now` - fetch a snapshot and return a
  student-friendly recommendation (structure + floor + explanation).

The functions are intentionally pure and easy to unit-test.
"""

from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .client import TitanParkError, fetch_parking_snapshot

logger = logging.getLogger(__name__)


@dataclass
class ParkingStructureSnapshot:
    """Normalized snapshot for a single parking structure.

    :param name: Human-readable structure name.
    :type name: str
    :param total_spots: Total number of spaces in the structure.
    :type total_spots: int
    :param available_spots: Currently free spaces.
    :type available_spots: int
    :param occupied_spots: Currently occupied spaces (may be derived).
    :type occupied_spots: int
    :param occupancy_rate: Fraction in ``[0.0, 1.0]`` of occupied spaces.
    :type occupancy_rate: float
    """

    name: str
    total_spots: int
    available_spots: int
    occupied_spots: int
    occupancy_rate: float


@dataclass
class ParkingRecommendation:
    """Result of a parking recommendation call.

    :param structure: Selected parking structure snapshot.
    :type structure: ParkingStructureSnapshot
    :param suggested_floor: Floor number students should try first.
        This is a heuristic, assuming the structure has *num_floors*
        (see :func:`recommend_parking_destination`).
    :type suggested_floor: int
    :param explanation: Human-readable text suitable for showing in the UI.
    :type explanation: str
    """

    structure: ParkingStructureSnapshot
    suggested_floor: int
    explanation: str


def normalize_structure_dict(raw: Dict[str, Any]) -> ParkingStructureSnapshot:
    """Convert a raw TitanPark structure dict into :class:`ParkingStructureSnapshot`.

    This helper understands a few common field names and falls back to
    reasonable defaults when values are missing.

    It supports both the original list-based payload with keys like
    ``total_spots`` / ``available_spots`` and the newer TitanPark
    mapping shape with keys like ``total`` / ``available`` / ``perc_full``.

    :param raw: Raw dictionary for a single structure (from
        :func:`titanpark_integration.client.fetch_parking_snapshot`).
    :type raw: dict[str, Any]
    :returns: Normalized snapshot instance.
    :rtype: ParkingStructureSnapshot
    :raises ValueError: If required fields such as ``total_spots`` or
        ``available_spots`` are missing or invalid.
    """
    # Name: support both "name" and "structure_name", with a fallback.  # Added Code
    name = (  #  Changed Code
        raw.get("name")  #  Changed Code
        or raw.get("structure_name")  #  Changed Code
        or str(raw.get("id", "Unknown Structure"))  #  Changed Code
    )  #  Changed Code

    # Total/available: handle both old (total_spots / available_spots)     # Added Code
    # and new (total / available) TitanPark keys.                          # Added Code
    try:  #  Changed Code
        total_value = raw.get("total_spots")  #  Changed Code
        if total_value is None:  #  Changed Code
            total_value = raw.get("total")  #  Changed Code
        available_value = raw.get("available_spots")  #  Changed Code
        if available_value is None:  #  Changed Code
            available_value = raw.get("available")  #  Changed Code

        total = int(total_value)  #  Changed Code
        available = int(available_value)  #  Changed Code
    except Exception as exc:  #  Changed Code
        raise ValueError(
            f"Invalid structure payload for {name!r}: {raw}"
        ) from exc  #  Changed Code

    # Occupied spots: use explicit field if present, otherwise derive.     # Added Code
    occupied_raw = raw.get("occupied_spots")  #  Changed Code
    if occupied_raw is None:  #  Changed Code
        occupied = max(total - available, 0)  #  Changed Code
    else:  #  Changed Code
        occupied = int(occupied_raw)  #  Changed Code

    # Occupancy rate: try explicit fields first (occupancy_rate / perc_full),  # Added Code
    # otherwise compute from occupied / total.                                  # Added Code
    rate: Optional[float] = None  # Added Code

    if "occupancy_rate" in raw:  # Added Code
        try:  # Added Code
            rate_candidate = float(raw["occupancy_rate"])  # Added Code
            # If backend gives 0–100, normalize to 0–1.                         # Added Code
            if rate_candidate > 1.0:  # Added Code
                rate_candidate /= 100.0  # Added Code
            rate = rate_candidate  # Added Code
        except Exception:  # Added Code
            rate = None  # Added Code
    elif "perc_full" in raw:  # Added Code
        try:  # Added Code
            perc_full = float(raw["perc_full"])  # Added Code
            rate = max(0.0, min(1.0, perc_full / 100.0))  # Added Code
        except Exception:  # Added Code
            rate = None  # Added Code

    if rate is None:  # Added Code
        if total <= 0:  # Added Code
            rate = 1.0  # Added Code
        else:  # Added Code
            rate = max(0.0, min(1.0, occupied / float(total)))  # Added Code

    return ParkingStructureSnapshot(  #  Changed Code
        name=name,  #  Changed Code
        total_spots=total,  #  Changed Code
        available_spots=available,  #  Changed Code
        occupied_spots=occupied,  #  Changed Code
        occupancy_rate=rate,  #  Changed Code
    )  #  Changed Code


def recommend_parking_destination(
    structures: Sequence[ParkingStructureSnapshot],
    preferred_structures: Optional[Sequence[str]] = None,
    min_free_ratio: float = 0.05,
    num_floors: int = 6,
) -> Optional[ParkingRecommendation]:
    """Choose a structure and suggested floor from a snapshot.

    The algorithm works in two steps:

    1. Filter out structures whose available-space ratio is below
       ``min_free_ratio``.
    2. Among the remaining ones, pick the structure with the
       highest ``available_spots``.

    A simple floor suggestion is computed by assuming *num_floors* floors
    and mapping the occupancy rate to "how high" you should drive:

    * low occupancy → lower floor numbers
    * high occupancy → upper floors
    """
    if not structures:
        return None
    candidates = list(structures)
    preferred_set = {s.strip().lower() for s in preferred_structures or []}
    if preferred_set:
        filtered = [s for s in candidates if s.name.strip().lower() in preferred_set]
        if filtered:
            candidates = filtered
    min_ratio = max(0.0, float(min_free_ratio))
    candidates = [
        s
        for s in candidates
        if s.total_spots > 0 and (s.available_spots / s.total_spots) >= min_ratio
    ]
    if not candidates:
        return None
    best = max(candidates, key=lambda s: s.available_spots)
    free_ratio = best.available_spots / float(best.total_spots or 1)
    free_ratio = max(0.0, min(1.0, free_ratio))
    occupied_fraction = 1.0 - free_ratio
    if num_floors <= 1:
        floor = 1
    else:
        floor = int(round(occupied_fraction * (num_floors - 1))) + 1
    explanation = (  #  Changed Code
        f"Recommended structure: {best.name}. "  #  Changed Code
        f"{best.available_spots} of {best.total_spots} spots are free "  #  Changed Code
        f"({free_ratio:.0%} availability). "  #  Changed Code
        f"Start by driving to floor {floor}; lower floors are likely to be "  #  Changed Code
        f"busier when the structure is this full."  #  Changed Code
    )  #  Changed Code
    return ParkingRecommendation(
        structure=best, suggested_floor=floor, explanation=explanation
    )


def recommend_parking_now(
    preferred_structures: Optional[Sequence[str]] = None,
    min_free_ratio: float = 0.05,
    num_floors: int = 6,
) -> Optional[ParkingRecommendation]:
    """Fetch a snapshot from TitanPark and return a recommendation.

    This is the main entry point your Tkinter GUI can call. A typical
    usage pattern inside a callback is::

        from titanpark_integration.recommendation import recommend_parking_now
        rec = recommend_parking_now(preferred_structures=["Nutwood Structure"])
        if rec is not None:
            label.config(text=rec.explanation)

    :param preferred_structures: Optional prioritized list of structure
        names; see :func:`recommend_parking_destination`.
    :type preferred_structures: sequence[str] | None
    :param min_free_ratio: Minimum fraction of free spaces for a structure
        to be considered acceptable.
    :type min_free_ratio: float
    :param num_floors: Assumed number of floors when computing
        *suggested_floor*.
    :type num_floors: int
    :returns: Recommendation instance, or ``None`` if no usable data
        is available.
    :rtype: ParkingRecommendation | None
    :raises TitanParkError: If the backend request fails.
    """
    raw_snapshot = fetch_parking_snapshot()
    snapshots: List[ParkingStructureSnapshot] = []
    for raw in raw_snapshot:
        try:
            snapshots.append(normalize_structure_dict(raw))
        except ValueError as exc:
            logger.warning("Skipping invalid structure payload: %s", exc)
    if not snapshots:
        logger.warning("No valid parking structures available in snapshot")
        return None
    return recommend_parking_destination(
        snapshots,
        preferred_structures=preferred_structures,
        min_free_ratio=min_free_ratio,
        num_floors=num_floors,
    )
