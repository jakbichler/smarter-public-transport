"""
Dijkstra-based route planner for public transport networks.

Builds a graph from GTFS data where each (parent_station_id, line_name) pair
is a node. Travel edges connect consecutive stations on the same line, and
transfer edges connect different lines at the same station.

Uses scipy.sparse.csgraph.dijkstra for shortest-path queries.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_array
from scipy.sparse.csgraph import dijkstra

# Route types to include (U-Bahn and S-Bahn)
VALID_ROUTE_TYPES = {400, 109}

GraphNode = tuple[str, str]  # (parent_station_id, line_name)


@dataclass
class RouteSegment:
    station_id: str
    station_name: str
    line: str


@dataclass
class RoutingResult:
    segments: list[RouteSegment]
    total_cost_seconds: float
    transfers: int


class TransitRouter:
    """Builds a static routing graph from GTFS data and answers shortest-path queries."""

    def __init__(
        self,
        gtfs_path: str | Path,
        line_names: list[str],
        default_transfer_seconds: float = 180.0,
    ):
        self._gtfs_path = Path(gtfs_path)
        self._line_names = line_names
        self._default_transfer_seconds = default_transfer_seconds

        # Node indexing
        self._node_to_idx: dict[GraphNode, int] = {}
        self._idx_to_node: list[GraphNode] = []

        # Station metadata
        self._station_names: dict[str, str] = {}  # parent_station_id -> name
        self._station_to_lines: dict[str, set[str]] = {}  # parent_station_id -> line names

        # Edges collected during build, then converted to CSR
        self._edge_rows: list[int] = []
        self._edge_cols: list[int] = []
        self._edge_weights: list[float] = []

        self._graph: csr_array | None = None

        self._build_graph()

    def _get_or_create_node(self, node: GraphNode) -> int:
        if node not in self._node_to_idx:
            idx = len(self._idx_to_node)
            self._node_to_idx[node] = idx
            self._idx_to_node.append(node)
        return self._node_to_idx[node]

    def _add_edge(self, from_node: GraphNode, to_node: GraphNode, cost: float) -> None:
        from_idx = self._get_or_create_node(from_node)
        to_idx = self._get_or_create_node(to_node)
        self._edge_rows.append(from_idx)
        self._edge_cols.append(to_idx)
        self._edge_weights.append(cost)

    def _parse_time(self, time_str: str) -> float:
        """Parse HH:MM:SS (including >24h) to seconds since midnight."""
        parts = time_str.strip().split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    def _build_graph(self) -> None:
        # Load GTFS data
        stops = pd.read_csv(
            self._gtfs_path / "stops.txt",
            usecols=["stop_id", "stop_name", "location_type", "parent_station"],
            dtype={"stop_id": str, "parent_station": str},
        )
        routes = pd.read_csv(
            self._gtfs_path / "routes.txt",
            usecols=["route_id", "route_short_name", "route_type"],
        )
        trips = pd.read_csv(
            self._gtfs_path / "trips.txt",
            usecols=["route_id", "trip_id", "direction_id"],
        )
        stop_times = pd.read_csv(
            self._gtfs_path / "stop_times.txt",
            usecols=["trip_id", "stop_id", "stop_sequence", "arrival_time", "departure_time"],
            dtype={"stop_id": str},
        )

        # Build platform -> parent_station mapping
        platform_to_parent: dict[str, str] = {}
        for _, row in stops.iterrows():
            sid = str(row["stop_id"])
            parent = row.get("parent_station")
            if pd.notna(parent) and parent:
                platform_to_parent[sid] = str(parent)
            else:
                platform_to_parent[sid] = sid

        # Build station name lookup (from location_type=1 rows)
        stations_df = stops[stops["location_type"] == 1]
        for _, row in stations_df.iterrows():
            self._station_names[str(row["stop_id"])] = str(row["stop_name"])

        # Also add names from platforms for stations without a type=1 entry
        for _, row in stops.iterrows():
            parent = platform_to_parent.get(str(row["stop_id"]), str(row["stop_id"]))
            if parent not in self._station_names:
                self._station_names[parent] = str(row["stop_name"])

        # Process each configured line
        for line_name in self._line_names:
            route_ids = self._resolve_route_ids(line_name, routes)
            if not route_ids:
                print(f"Warning: No valid routes found for {line_name}")
                continue

            # Filter trips to only those belonging to this line's routes
            line_trips = trips[trips["route_id"].isin(route_ids)]

            for direction in [0, 1]:
                dir_trips = line_trips[line_trips["direction_id"] == direction]
                if dir_trips.empty:
                    continue

                rep_trip_id = self._pick_representative_trip(dir_trips, stop_times)
                if rep_trip_id is None:
                    continue

                self._add_travel_edges(
                    line_name, rep_trip_id, stop_times, platform_to_parent
                )

        # Build transfer edges
        self._add_transfer_edges()

        # Build CSR matrix
        n = len(self._idx_to_node)
        if n == 0:
            self._graph = csr_array((0, 0))
            return

        self._graph = csr_array(
            (
                np.array(self._edge_weights),
                (np.array(self._edge_rows), np.array(self._edge_cols)),
            ),
            shape=(n, n),
        )

        # Free temporary edge lists
        self._edge_rows.clear()
        self._edge_cols.clear()
        self._edge_weights.clear()

    def _resolve_route_ids(self, line_name: str, routes: pd.DataFrame) -> list[str]:
        """Get valid route_ids for a line name, filtering out bus replacements."""
        matches = routes[
            (routes["route_short_name"] == line_name)
            & (routes["route_type"].isin(VALID_ROUTE_TYPES))
        ]
        return matches["route_id"].tolist()

    def _pick_representative_trip(
        self, dir_trips: pd.DataFrame, stop_times: pd.DataFrame
    ) -> int | None:
        """Pick the trip with the most stops."""
        trip_ids = dir_trips["trip_id"]
        counts = stop_times[stop_times["trip_id"].isin(trip_ids)].groupby("trip_id").size()
        if counts.empty:
            return None
        return counts.idxmax()

    def _add_travel_edges(
        self,
        line_name: str,
        trip_id: int,
        stop_times: pd.DataFrame,
        platform_to_parent: dict[str, str],
    ) -> None:
        """Add travel edges for consecutive stops on a trip."""
        trip_st = stop_times[stop_times["trip_id"] == trip_id].sort_values("stop_sequence")

        prev_parent: str | None = None
        prev_dep: float | None = None

        for _, row in trip_st.iterrows():
            stop_id = str(row["stop_id"])
            parent = platform_to_parent.get(stop_id, stop_id)
            arr = self._parse_time(str(row["arrival_time"]))
            dep = self._parse_time(str(row["departure_time"]))

            # Track which lines serve each station
            self._station_to_lines.setdefault(parent, set()).add(line_name)

            if prev_parent is not None and prev_dep is not None and parent != prev_parent:
                cost = arr - prev_dep
                if cost > 0:
                    self._add_edge((prev_parent, line_name), (parent, line_name), cost)

            prev_parent = parent
            prev_dep = dep

    def _add_transfer_edges(self) -> None:
        """Add transfer edges between lines at shared stations."""
        for station_id, lines in self._station_to_lines.items():
            if len(lines) < 2:
                continue
            line_list = sorted(lines)
            for i, line_a in enumerate(line_list):
                for line_b in line_list[i + 1 :]:
                    node_a = (station_id, line_a)
                    node_b = (station_id, line_b)
                    # Bidirectional transfer
                    self._add_edge(node_a, node_b, self._default_transfer_seconds)
                    self._add_edge(node_b, node_a, self._default_transfer_seconds)

    def find_route(
        self, origin_station_id: str, dest_station_id: str
    ) -> RoutingResult | None:
        """Find shortest route between two parent station IDs."""
        if origin_station_id == dest_station_id:
            name = self._station_names.get(origin_station_id, origin_station_id)
            lines = self._station_to_lines.get(origin_station_id, set())
            line = next(iter(lines)) if lines else ""
            return RoutingResult(
                segments=[RouteSegment(origin_station_id, name, line)],
                total_cost_seconds=0.0,
                transfers=0,
            )

        if self._graph is None or self._graph.shape[0] == 0:
            return None

        # Multi-source: all (origin, line) nodes
        source_indices = [
            self._node_to_idx[(origin_station_id, line)]
            for line in self._station_to_lines.get(origin_station_id, set())
            if (origin_station_id, line) in self._node_to_idx
        ]
        if not source_indices:
            return None

        # Destination node indices
        dest_indices = [
            self._node_to_idx[(dest_station_id, line)]
            for line in self._station_to_lines.get(dest_station_id, set())
            if (dest_station_id, line) in self._node_to_idx
        ]
        if not dest_indices:
            return None

        dist_matrix, predecessors, _sources = dijkstra(
            csgraph=self._graph,
            directed=True,
            indices=source_indices,
            return_predecessors=True,
            min_only=True,
        )

        # Find best destination node
        best_dest_idx = None
        best_cost = np.inf
        for di in dest_indices:
            if dist_matrix[di] < best_cost:
                best_cost = dist_matrix[di]
                best_dest_idx = di

        if best_dest_idx is None or np.isinf(best_cost):
            return None

        # Reconstruct path
        path_indices: list[int] = []
        current = best_dest_idx
        while current != -9999:
            path_indices.append(current)
            pred = predecessors[current]
            if pred == current:
                break
            current = pred

        path_indices.reverse()

        # Convert to segments
        segments: list[RouteSegment] = []
        transfers = 0
        prev_line: str | None = None

        for idx in path_indices:
            station_id, line = self._idx_to_node[idx]
            name = self._station_names.get(station_id, station_id)
            segments.append(RouteSegment(station_id, name, line))
            if prev_line is not None and line != prev_line:
                transfers += 1
            prev_line = line

        return RoutingResult(
            segments=segments,
            total_cost_seconds=float(best_cost),
            transfers=transfers,
        )

    def get_lines_at_station(self, station_id: str) -> list[str]:
        """Get all line names serving a parent station."""
        return sorted(self._station_to_lines.get(station_id, set()))

    def get_all_station_ids(self) -> set[str]:
        """Get all parent station IDs in the graph."""
        return set(self._station_to_lines.keys())
