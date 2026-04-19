"""
Train class with mutable state for simulation.
"""

import math
from enum import Enum

from src.core.line import Line


class TrainState(Enum):
    """Possible states for a train."""

    AT_STATION = "at_station"
    TRAVELING = "traveling"


class Train:
    """
    Train operating on a line - mutable state object for simulation.

    Unlike Station and Line, Train has mutable state that changes during simulation.
    """

    def __init__(
        self,
        train_id: str,
        line: Line,
        speed_kmh: float | None = None,
        capacity: int = 100,
        initial_station_index: int = 0,
    ):
        """
        Initialize a train.

        Args:
            train_id: Unique identifier for this train
            line: The line this train operates on
            speed_kmh: Speed in km/h (defaults to line's speed)
            capacity: Maximum passenger capacity
            initial_station_index: Starting station index on the line
        """
        self.id = train_id
        self.line = line
        self.speed_kmh = speed_kmh if speed_kmh is not None else line.speed_kmh
        self.capacity = capacity

        # Mutable state
        self.current_station_index: int = initial_station_index
        self.next_station_index: int = initial_station_index + 1
        self.progress_km: float = 0.0  # Progress along current segment
        self.state: TrainState = TrainState.AT_STATION
        self.dwell_time_remaining: float = 0.0
        self.passengers: list = []  # List of passenger objects (to be implemented)

        # Direction (1 for forward, -1 for backward)
        self.direction: int = 1

        # Position tracking for orientation
        self.last_lat: float | None = None
        self.last_lon: float | None = None
        self.current_angle: float = 0.0  # Angle in degrees (0 = north, clockwise)

    @property
    def current_station(self):
        """Get the current station object."""
        return self.line.stations[self.current_station_index]

    @property
    def next_station(self):
        """Get the next station object."""
        if self.next_station_index < len(self.line.stations):
            return self.line.stations[self.next_station_index]
        return None

    @property
    def segment_distance_km(self) -> float:
        """Get the distance of the current segment being traversed."""
        if self.next_station is None:
            return 0.0
        return self.line.distance_between_stations(
            self.current_station_index, self.next_station_index
        )

    @property
    def progress_fraction(self) -> float:
        """Get progress along current segment as fraction (0.0 to 1.0)."""
        segment_dist = self.segment_distance_km
        if segment_dist == 0:
            return 0.0
        return min(1.0, self.progress_km / segment_dist)

    @property
    def passenger_count(self) -> int:
        """Get current number of passengers on the train."""
        return len(self.passengers)

    @property
    def available_capacity(self) -> int:
        """Get remaining capacity."""
        return max(0, self.capacity - self.passenger_count)

    @property
    def load_factor(self) -> float:
        """Get load factor (0.0 to 1.0+)."""
        return self.passenger_count / self.capacity if self.capacity > 0 else 0.0

    def update_position(self, lat: float, lon: float):
        """
        Update train's position and calculate orientation angle.

        Args:
            lat: Current latitude
            lon: Current longitude
        """
        if self.last_lat is not None and self.last_lon is not None:
            # Calculate delta
            delta_lat = lat - self.last_lat
            delta_lon = lon - self.last_lon

            # Only update angle if there's meaningful movement (avoid noise)
            if abs(delta_lat) > 1e-2 or abs(delta_lon) > 1e-2:
                # Calculate angle: atan2 gives angle from east, we want from north
                # atan2(delta_lon, delta_lat) gives angle from north in radians
                angle_rad = math.atan2(delta_lon, delta_lat)
                # Convert to degrees (0 = north, clockwise positive)
                self.current_angle = math.degrees(angle_rad)

        # Update last position
        self.last_lat = lat
        self.last_lon = lon

    def update(self, dt: float, base_dwell_time: float = 20.0):
        """
        Update train state for one time step.

        Args:
            dt: Time step in seconds
            base_dwell_time: Base dwell time at stations in seconds
        """
        if self.state == TrainState.TRAVELING:
            self._update_traveling(dt)
        elif self.state == TrainState.AT_STATION:
            self._update_at_station(dt, base_dwell_time)

    def _update_traveling(self, dt: float):
        """Update train position while traveling."""
        # Convert speed to km/s
        speed_kms = self.speed_kmh / 3600.0

        # Update progress
        self.progress_km += speed_kms * dt

        # Check if arrived at next station
        if self.progress_km >= self.segment_distance_km:
            self._arrive_at_station()

    def _arrive_at_station(self):
        """Handle arrival at a station."""
        self.current_station_index = self.next_station_index
        self.progress_km = 0.0
        self.state = TrainState.AT_STATION

        # Set dwell time (will be handled in update_at_station)
        # For now, we'll set it in the update method

    def _update_at_station(self, dt: float, base_dwell_time: float):
        """Update train state while at a station."""
        if self.dwell_time_remaining <= 0:
            # Just arrived, set dwell time
            self.dwell_time_remaining = base_dwell_time
            # Handle passenger boarding/alighting here (to be implemented)

        # Count down dwell time
        self.dwell_time_remaining -= dt

        # Check if ready to depart
        if self.dwell_time_remaining <= 0:
            self._depart_station()

    def _depart_station(self):
        """Handle departure from a station."""
        # Determine next station
        if self.direction == 1:
            # Moving forward
            if self.current_station_index < len(self.line.stations) - 1:
                self.next_station_index = self.current_station_index + 1
                self.state = TrainState.TRAVELING
                self.progress_km = 0.0
            else:
                # Reached end of line, reverse direction
                self.direction = -1
                self.next_station_index = self.current_station_index - 1
                self.state = TrainState.TRAVELING
                self.progress_km = 0.0
        else:
            # Moving backward
            if self.current_station_index > 0:
                self.next_station_index = self.current_station_index - 1
                self.state = TrainState.TRAVELING
                self.progress_km = 0.0
            else:
                # Reached start of line, reverse direction
                self.direction = 1
                self.next_station_index = self.current_station_index + 1
                self.state = TrainState.TRAVELING
                self.progress_km = 0.0

    def __str__(self) -> str:
        return (
            f"Train({self.id} on {self.line.name}, "
            f"{self.state.value}, "
            f"{self.passenger_count}/{self.capacity} passengers)"
        )

    def __repr__(self) -> str:
        return (
            f"Train(id='{self.id}', line='{self.line.name}', "
            f"station={self.current_station.name}, state={self.state.value})"
        )
