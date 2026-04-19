"""
Station class using Pydantic for validation and immutability.
"""

from pydantic import BaseModel, Field


class Station(BaseModel):
    """
    Transit station with validated geographic coordinates.

    Stations are immutable - their location and properties don't change during simulation.
    """

    id: str = Field(
        ...,
        min_length=1,
        description="Unique station identifier (e.g., 'U8_900120003')",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable station name (e.g., 'Alexanderplatz (Berlin)')",
    )
    display_name: str = Field(
        ...,
        min_length=1,
        description="Name to display on maps (e.g., 'Alexanderplatz')",
    )
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in degrees")

    model_config = {"frozen": True}  # Make immutable (Pydantic v2 syntax)

    @property
    def position(self) -> tuple[float, float]:
        """Returns (lat, lon) tuple for convenience."""
        return (self.lat, self.lon)

    def __str__(self) -> str:
        return f"Station({self.name} at {self.lat:.4f}, {self.lon:.4f})"

    def __repr__(self) -> str:
        return f"Station(id='{self.id}', name='{self.name}', lat={self.lat}, lon={self.lon})"
