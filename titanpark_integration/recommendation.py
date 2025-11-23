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
    #  STUB: return a dummy snapshot; students should normalize the real dict.
    return ParkingStructureSnapshot(
        name="Dummy Structure",
        total_spots=0,
        available_spots=0,
        occupied_spots=0,
        occupancy_rate=0.0,
    )


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
    #  STUB: no recommendation yet; students should implement the selection logic.
    return None


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
    #  STUB: return no recommendation; students should call the client and compute a result.
    return None
