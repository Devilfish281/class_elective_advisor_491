"""TitanPark integration package for Smart Elective Advisor.

This package provides a small, well-documented API for talking to the
TitanPark FastAPI backend and computing high-level parking recommendations
for CSUF students.
"""

from .client import (
    fetch_parking_snapshot,
    fetch_structure_details,
    find_structure_snapshot,
)
from .config import get_titanpark_base_url, get_titanpark_timeout
from .recommendation import (
    ParkingRecommendation,
    ParkingStructureSnapshot,
    recommend_parking_destination,
    recommend_parking_now,
)

__all__ = [
    "get_titanpark_base_url",
    "get_titanpark_timeout",
    "fetch_parking_snapshot",
    "find_structure_snapshot",
    "fetch_structure_details",
    "ParkingStructureSnapshot",
    "ParkingRecommendation",
    "recommend_parking_destination",
    "recommend_parking_now",
]
