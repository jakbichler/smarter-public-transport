"""
Core simulator for public transport network simulation.
"""

from src.core.config import SimulationConfig
from src.core.line import Line
from src.core.passenger import Passenger
from src.core.train import Train
from src.data.gtfs_loader import GTFSLoader


class Simulator:
    """
    Main simulation engine for public transport networks.

    Manages trains, updates their positions, and tracks simulation time.
    """

    def __init__(self, config: SimulationConfig):
        """
        Initialize the simulator.

        Args:
            config: Simulation configuration
        """
        self.config = config
        self.time: float = 0.0  # Simulation time in seconds
        self.dt: float = config.time_step_seconds

        # Load GTFS data
        self.gtfs_loader = GTFSLoader(config.gtfs_path)

        # Load lines
        self.lines: dict[str, Line] = {}
        for line_name in config.ubahn_lines:
            try:
                line = self.gtfs_loader.create_line(line_name, config.train_speed_kmh)
                self.lines[line_name] = line
                print(f"Loaded line: {line}")
            except Exception as e:
                print(f"Warning: Could not load line {line_name}: {e}")

        # Create trains
        self.trains: list[Train] = []
        self._spawn_trains()

        # Spawn initial passengers
        self.passengers: list[Passenger] = []
        self._spawn_random_passenger_same_line()

    def _spawn_trains(self):
        """Spawn trains on all lines according to configuration."""
        train_counter = 0
        for line_name, line in self.lines.items():
            for i in range(self.config.trains_per_line):
                # Distribute trains evenly along the line
                initial_station = i * (
                    len(line.stations) // self.config.trains_per_line
                )
                initial_station = min(initial_station, len(line.stations) - 1)

                train = Train(
                    train_id=f"{line_name}_T{train_counter}",
                    line=line,
                    speed_kmh=self.config.train_speed_kmh,
                    capacity=100,  # Default capacity
                    initial_station_index=initial_station,
                )
                self.trains.append(train)
                train_counter += 1
                print(f"Spawned train: {train}")

    def _spawn_random_passenger_same_line(self):
        """Spawn a random passenger wanting to travel on the same line."""
        import random

        if not self.lines:
            raise ValueError("No lines available to spawn passengers.")

        for _ in range(self.config.initial_passengers):
            line = random.choice(list(self.lines.values()))
            if len(line.stations) < 2:
                continue

            origin, destination = random.sample(line.stations, 2)
            passenger = Passenger(
                id=f"P{len(self.passengers)}",
                origin_station_id=origin.id,
                destination_station_id=destination.id,
                current_station_id=origin.id,
            )
            self.passengers.append(passenger)
            print(f"Spawned passenger: {passenger}")

    def step(self):
        """Execute one simulation time step."""
        # Update all trains
        for train in self.trains:
            train.update(self.dt, self.config.dwell_time_seconds)

        # Advance simulation time
        self.time += self.dt

    def reset(self):
        """Reset simulation to initial state."""
        self.time = 0.0
        self.trains.clear()
        self._spawn_trains()

    def get_train_positions(self) -> list[dict]:
        """
        Get current positions of all trains for visualization.

        Returns:
            List of dictionaries with train position data
        """
        positions = []
        for train in self.trains:
            if train.state.value == "traveling" and train.next_station is not None:
                # Interpolate position between stations
                from src.utils.geometry import interpolate_position

                current = train.current_station
                next_station = train.next_station
                lat, lon = interpolate_position(
                    current.lat,
                    current.lon,
                    next_station.lat,
                    next_station.lon,
                    train.progress_fraction,
                )
                # Include next station for angle calculation
                next_station_lat = next_station.lat
                next_station_lon = next_station.lon
            else:
                # At station
                lat, lon = train.current_station.lat, train.current_station.lon
                # When at station, use the next station for orientation
                if train.next_station is not None:
                    next_station_lat = train.next_station.lat
                    next_station_lon = train.next_station.lon
                else:
                    next_station_lat = None
                    next_station_lon = None

            positions.append(
                {
                    "id": train.id,
                    "lat": lat,
                    "lon": lon,
                    "next_station_lat": next_station_lat,
                    "next_station_lon": next_station_lon,
                    "line": train.line.name,
                    "color": train.line.color,
                    "state": train.state.value,
                    "passenger_count": train.passenger_count,
                    "capacity": train.capacity,
                    "load_factor": train.load_factor,
                    "train": train,  # Pass train object reference
                }
            )

        return positions

    def get_passengers_by_station(self) -> dict[str, int]:
        """
        Get count of passengers waiting at each station.

        Returns:
            Dictionary mapping station_id to passenger count
        """
        station_passengers: dict[str, int] = {}
        for passenger in self.passengers:
            station_id = passenger.current_station_id
            station_passengers[station_id] = station_passengers.get(station_id, 0) + 1
        return station_passengers

    def get_statistics(self) -> dict:
        """Get simulation statistics."""
        total_passengers = sum(train.passenger_count for train in self.trains)
        avg_load_factor = (
            sum(train.load_factor for train in self.trains) / len(self.trains)
            if self.trains
            else 0
        )

        return {
            "time": self.time,
            "num_trains": len(self.trains),
            "num_lines": len(self.lines),
            "total_passengers": total_passengers,
            "avg_load_factor": avg_load_factor,
        }

    def __str__(self) -> str:
        stats = self.get_statistics()
        return (
            f"Simulator(t={stats['time']:.1f}s, "
            f"{stats['num_trains']} trains, "
            f"{stats['num_lines']} lines, "
            f"{stats['total_passengers']} passengers)"
        )
