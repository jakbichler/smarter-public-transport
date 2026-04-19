"""
Line class using Pydantic for validation and immutability.
"""

from pydantic import BaseModel, Field, field_validator

from src.core.station import Station
from src.utils.geometry import calculate_distance


class Line(BaseModel):
    """
    Transit line connecting multiple stations.

    Lines are immutable - the route and station sequence don't change during simulation.
    """

    id: str = Field(..., min_length=1, description="Unique line identifier (e.g., 'U8')")
    name: str = Field(..., min_length=1, description="Human-readable line name (e.g., 'U8')")
    stations: list[Station] = Field(
        ..., min_length=2, description="Ordered list of stations on this line"
    )
    speed_kmh: float = Field(
        default=30.0, gt=0, le=100, description="Default speed for trains on this line in km/h"
    )
    color: str = Field(default="#000000", description="Color for visualization (hex code)")

    model_config = {"frozen": True}  # Make immutable

    @field_validator("stations")
    @classmethod
    def stations_must_be_unique(cls, v: list[Station]) -> list[Station]:
        """Ensure no duplicate stations on the line."""
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate stations found in line")
        return v

    @property
    def total_length_km(self) -> float:
        """Calculate total length of the line in kilometers."""
        total = 0.0
        for i in range(len(self.stations) - 1):
            total += calculate_distance(
                self.stations[i].lat,
                self.stations[i].lon,
                self.stations[i + 1].lat,
                self.stations[i + 1].lon,
            )
        return total

    def distance_between_stations(self, index1: int, index2: int) -> float:
        """
        Calculate distance between two adjacent stations.

        Args:
            index1: Index of first station
            index2: Index of second station (should be index1 + 1)

        Returns:
            Distance in kilometers
        """
        if abs(index2 - index1) != 1:
            raise ValueError("Can only calculate distance between adjacent stations")
        i = min(index1, index2)
        return calculate_distance(
            self.stations[i].lat,
            self.stations[i].lon,
            self.stations[i + 1].lat,
            self.stations[i + 1].lon,
        )

    def get_station_by_id(self, station_id: str) -> Station | None:
        """Get station by its ID."""
        for station in self.stations:
            if station.id == station_id:
                return station
        return None

    def get_station_index(self, station_id: str) -> int:
        """Get the index of a station by its ID. Returns -1 if not found."""
        for i, station in enumerate(self.stations):
            if station.id == station_id:
                return i
        return -1

    def __str__(self) -> str:
        return f"Line({self.name}: {len(self.stations)} stations, {self.total_length_km:.2f} km)"

    def __repr__(self) -> str:
        station_names = [s.name for s in self.stations]
        return f"Line(id='{self.id}', name='{self.name}', stations={station_names})"
