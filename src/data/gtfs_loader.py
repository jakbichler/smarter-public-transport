"""
GTFS data loader for Berlin public transport network.
"""

from pathlib import Path

import pandas as pd

from src.core.line import Line
from src.core.station import Station


class GTFSLoader:
    """Load and parse GTFS data for Berlin U-Bahn."""

    def __init__(self, gtfs_path: str | Path):
        """
        Initialize GTFS loader.

        Args:
            gtfs_path: Path to directory containing GTFS files
        """
        self.gtfs_path = Path(gtfs_path)

        # Load GTFS files
        self.stops = self._load_stops()
        self.routes = self._load_routes()
        self.trips = self._load_trips()
        self.stop_times = self._load_stop_times()

    def _load_stops(self) -> pd.DataFrame:
        """Load stops.txt"""
        stops_file = self.gtfs_path / "stops.txt"
        if not stops_file.exists():
            raise FileNotFoundError(f"stops.txt not found in {self.gtfs_path}")
        return pd.read_csv(stops_file)

    def _load_routes(self) -> pd.DataFrame:
        """Load routes.txt"""
        routes_file = self.gtfs_path / "routes.txt"
        if not routes_file.exists():
            raise FileNotFoundError(f"routes.txt not found in {self.gtfs_path}")
        return pd.read_csv(routes_file)

    def _load_trips(self) -> pd.DataFrame:
        """Load trips.txt"""
        trips_file = self.gtfs_path / "trips.txt"
        if not trips_file.exists():
            raise FileNotFoundError(f"trips.txt not found in {self.gtfs_path}")
        return pd.read_csv(trips_file)

    def _load_stop_times(self) -> pd.DataFrame:
        """Load stop_times.txt"""
        stop_times_file = self.gtfs_path / "stop_times.txt"
        if not stop_times_file.exists():
            raise FileNotFoundError(f"stop_times.txt not found in {self.gtfs_path}")
        return pd.read_csv(stop_times_file)

    def get_ubahn_routes(self) -> pd.DataFrame:
        """Get all U-Bahn routes (filter by route_short_name starting with 'U')."""
        ubahn_routes = self.routes[self.routes["route_short_name"].str.startswith("U")]
        return ubahn_routes

    def get_route_by_name(self, route_name: str) -> pd.Series | None:
        """
        Get route information by name (e.g., 'U8').

        Args:
            route_name: Route short name (e.g., 'U8')

        Returns:
            Route information as pandas Series, or None if not found
        """
        matches = self.routes[self.routes["route_short_name"] == route_name]
        if len(matches) == 0:
            return None
        return matches.iloc[0]

    def get_stops_for_route(
        self, route_name: str
    ) -> list[tuple[str, str, float, float]]:
        """
        Get ordered list of stops for a route.

        Args:
            route_name: Route short name (e.g., 'U8')

        Returns:
            List of tuples: (stop_id, stop_name, lat, lon) in order
        """
        # Get route
        route = self.get_route_by_name(route_name)
        if route is None:
            raise ValueError(f"Route {route_name} not found")

        route_id = route["route_id"]

        # Get trips for this route
        route_trips = self.trips[self.trips["route_id"] == route_id]
        if len(route_trips) == 0:
            raise ValueError(f"No trips found for route {route_name}")

        # Get the first trip (assuming all trips have the same stop sequence)
        trip_id = route_trips.iloc[0]["trip_id"]

        # Get stop times for this trip
        trip_stop_times = self.stop_times[self.stop_times["trip_id"] == trip_id]
        trip_stop_times = trip_stop_times.sort_values("stop_sequence")

        # Get stop details
        stops_list = []
        for _, stop_time in trip_stop_times.iterrows():
            stop_id = stop_time["stop_id"]
            stop = self.stops[self.stops["stop_id"] == stop_id].iloc[0]
            stops_list.append(
                (
                    str(stop["stop_id"]),
                    str(stop["stop_name"]),
                    float(stop["stop_lat"]),
                    float(stop["stop_lon"]),
                )
            )

        return stops_list

    def create_line(self, route_name: str, speed_kmh: float = 30.0) -> Line:
        """
        Create a Line object from GTFS data.

        Args:
            route_name: Route short name (e.g., 'U8')
            speed_kmh: Default speed for trains on this line

        Returns:
            Line object with stations loaded from GTFS
        """
        # Get route info
        route = self.get_route_by_name(route_name)
        if route is None:
            raise ValueError(f"Route {route_name} not found")

        # Get stops
        stops_data = self.get_stops_for_route(route_name)

        # Create Station objects
        stations = []
        for stop_id, stop_name, lat, lon in stops_data:
            display_name = self.convert_station_name_to_display_name(stop_name)
            station = Station(
                id=stop_id, name=stop_name, display_name=display_name, lat=lat, lon=lon
            )
            stations.append(station)

        # Get color from route (if available)
        color = (
            f"#{route['route_color']}"
            if "route_color" in route and pd.notna(route["route_color"])
            else "#000000"
        )

        # Create Line object
        line = Line(
            id=route["route_id"],
            name=route_name,
            stations=stations,
            speed_kmh=speed_kmh,
            color=color,
        )

        return line

    def list_available_routes(self) -> list[str]:
        """List all available U-Bahn routes."""
        ubahn = self.get_ubahn_routes()
        return ubahn["route_short_name"].tolist()

    def convert_station_name_to_display_name(self, station_name: str) -> str:
        """
        Convert full station name to display name by removing parenthetical info.

        Args:
            station_name: Full station name (e.g., 'Alexanderplatz (Berlin)')

        Returns:
            Display name (e.g., 'Alexanderplatz')
        """
        if "(" in station_name:
            return station_name.partition("(")[0].strip()
        return station_name
