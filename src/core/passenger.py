from pydantic import BaseModel, Field


class Passenger(BaseModel):
    """Passenger class using Pydantic validation"""

    id: str = Field(
        ...,
        min_length=1,
        description="Unique passenger identifier",
    )
    origin_station_id: str = Field(
        ...,
        min_length=1,
        description="ID of the origin station",
    )
    destination_station_id: str = Field(
        ...,
        min_length=1,
        description="ID of the destination station",
    )

    current_station_id: str | None = Field(
        default=None,
        description="ID of the current station (None if in transit)",
    )

    def __str__(self) -> str:
        return f"Passenger({self.id} from {self.origin_station_id} to {self.destination_station_id})"

    def __repr__(self) -> str:
        return f"Passenger(id='{self.id}', origin_station_id='{self.origin_station_id}', destination_station_id='{self.destination_station_id}')"
