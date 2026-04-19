"""
Pygame-based visualizer for public transport simulation.
"""

import math

import numpy as np
import pygame

from src.core.config import VisualizationConfig
from src.simulation.simulator import Simulator


class PygameVisualizer:
    """
    Interactive visualization of public transport simulation using Pygame.
    """

    def __init__(self, simulator: Simulator, config: VisualizationConfig):
        """
        Initialize the visualizer.

        Args:
            simulator: The simulator to visualize
            config: Visualization configuration
        """
        self.simulator = simulator
        self.config = config

        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.window_width, config.window_height)
        )
        pygame.display.set_caption("Public Transport Simulation")

        # Clock for FPS control
        self.clock = pygame.time.Clock()

        # Font for text rendering
        self.font = pygame.font.SysFont("Arial", 6)
        self.title_font = pygame.font.SysFont("Arial", 20, bold=True)

        # Parse colors
        self.bg_color = self._parse_color(config.background_color)
        self.station_color = self._parse_color(config.station_color)
        self.text_color = self._parse_color(config.text_color)

        # Calculate map bounds and scaling
        self._calculate_map_bounds()

        # Running state
        self.running = True
        self.paused = False

    def _parse_color(self, hex_color: str) -> tuple[int, int, int]:
        """Parse hex color string to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def _calculate_map_bounds(self):
        """Calculate geographic bounds and scaling factors (vectorized with NumPy)."""
        # Collect all station coordinates (vectorized)
        coords = np.array(
            [
                (station.lat, station.lon)
                for line in self.simulator.lines.values()
                for station in line.stations
            ]
        )

        if len(coords) == 0:
            # Default to Berlin center if no stations
            self.min_lat, self.max_lat = 52.4, 52.6
            self.min_lon, self.max_lon = 13.2, 13.5
        else:
            # Calculate bounds with 10% padding (vectorized)
            lats, lons = coords[:, 0], coords[:, 1]
            lat_range = np.ptp(lats)  # peak-to-peak = max - min
            lon_range = np.ptp(lons)

            self.min_lat = lats.min() - lat_range * 0.1
            self.max_lat = lats.max() + lat_range * 0.1
            self.min_lon = lons.min() - lon_range * 0.1
            self.max_lon = lons.max() + lon_range * 0.1

        # Calculate scaling (reserve space for UI)
        self.map_width = self.config.window_width - 40
        self.map_height = self.config.window_height - 100
        self.map_offset_x = 20
        self.map_offset_y = 60

    def _geo_to_screen(self, lat: float, lon: float) -> tuple[int, int]:
        """Convert geographic coordinates to screen coordinates."""
        # Normalize to [0, 1]
        x_norm = (
            (lon - self.min_lon) / (self.max_lon - self.min_lon)
            if self.max_lon != self.min_lon
            else 0.5
        )
        y_norm = (
            (lat - self.min_lat) / (self.max_lat - self.min_lat)
            if self.max_lat != self.min_lat
            else 0.5
        )

        # Scale to screen (flip Y axis)
        screen_x = int(self.map_offset_x + x_norm * self.map_width)
        screen_y = int(self.map_offset_y + (1 - y_norm) * self.map_height)

        return screen_x, screen_y

    def _draw_lines(self):
        """Draw all transit lines."""
        for line in self.simulator.lines.values():
            color = self._parse_color(line.color)

            # Draw line segments
            for i in range(len(line.stations) - 1):
                start_pos = self._geo_to_screen(
                    line.stations[i].lat, line.stations[i].lon
                )
                end_pos = self._geo_to_screen(
                    line.stations[i + 1].lat, line.stations[i + 1].lon
                )
                pygame.draw.line(self.screen, color, start_pos, end_pos, 2)

    def _draw_stations(self):
        """Draw all stations."""
        for line in self.simulator.lines.values():
            for station in line.stations:
                pos = self._geo_to_screen(station.lat, station.lon)

                # Draw station circle
                pygame.draw.circle(
                    self.screen, self.station_color, pos, self.config.station_radius
                )
                pygame.draw.circle(
                    self.screen, self.bg_color, pos, self.config.station_radius - 2
                )

                # Draw short station label (first 4 letters)
                label = station.name[:4]
                text = self.font.render(label, True, self.text_color)
                self.screen.blit(text, (pos[0] + 10, pos[1] - 7))

    def _draw_passengers_at_station(self):
        """Draw passengers waiting at stations as small red squares stacked in columns."""
        # Get unique stations across all lines
        drawn_stations = set()
        passenger_at_stations = self.simulator.get_passengers_by_station()

        for line in self.simulator.lines.values():
            for station in line.stations:
                # Skip if we already drew passengers for this station
                if station.id in drawn_stations:
                    continue
                drawn_stations.add(station.id)

                # Get number of passengers at this station
                num_passengers = passenger_at_stations.get(station.id, 0)

                if num_passengers == 0:
                    continue

                pos = self._geo_to_screen(station.lat, station.lon)

                # Configuration for passenger squares
                square_size = 3  # Small red squares
                spacing = 1  # Space between squares
                max_per_column = 10  # Stack up to 10 before starting new column
                passenger_per_square = 10  # Each square represents 10 passengers

                for i in range(max(1, num_passengers // passenger_per_square)):
                    column = i // max_per_column
                    row = i % max_per_column

                    # Calculate position (offset from station position)
                    x = pos[0] + column * (square_size + spacing) + 10
                    y = pos[1] - row * (square_size + spacing) - 5

                    # Draw small red square
                    rect = pygame.Rect(x, y, square_size, square_size)
                    pygame.draw.rect(self.screen, (255, 0, 0), rect)

    def _smooth_angle(
        self, current_angle: float, target_angle: float, smoothing: float = 0.1
    ) -> float:
        """
        Smooth angle transition using exponential moving average.

        Args:
            current_angle: Current angle in degrees
            target_angle: Target angle in degrees
            smoothing: Smoothing factor (0-1), lower = smoother

        Returns:
            Smoothed angle in degrees
        """
        # Calculate angle difference, handling wrapping
        diff = target_angle - current_angle

        # Normalize difference to [-180, 180]
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        # Apply exponential smoothing
        new_angle = current_angle + smoothing * diff

        # Normalize to [0, 360)
        return new_angle % 360

    def _draw_trains(self):
        """Draw all trains."""
        train_positions = self.simulator.get_train_positions()

        for train_pos in train_positions:
            # Convert current position to screen coordinates
            screen_x, screen_y = self._geo_to_screen(train_pos["lat"], train_pos["lon"])
            color = self._parse_color(train_pos["color"])

            # Calculate angle based on screen coordinates
            train = train_pos["train"]

            if (
                train_pos["next_station_lat"] is not None
                and train_pos["next_station_lon"] is not None
            ):
                # Convert next station to screen coordinates
                next_screen_x, next_screen_y = self._geo_to_screen(
                    train_pos["next_station_lat"], train_pos["next_station_lon"]
                )

                # Calculate angle in screen space
                delta_x = next_screen_x - screen_x
                delta_y = next_screen_y - screen_y

                # atan2(x, -y) because screen Y increases downward
                # This gives 0 = up, clockwise positive
                if abs(delta_x) > 0.1 or abs(delta_y) > 0.1:
                    target_angle = math.degrees(math.atan2(delta_x, -delta_y))

                    # Smooth the angle transition
                    if hasattr(train, "current_angle"):
                        angle = self._smooth_angle(train.current_angle, target_angle)
                    else:
                        # First time, set directly
                        angle = target_angle

                    # Store smoothed angle in train for persistence
                    train.current_angle = angle
                else:
                    # Not enough movement, use stored angle
                    angle = train.current_angle
            else:
                # No next station, use stored angle or default
                angle = train.current_angle

            # Create a surface for the train
            train_surface = pygame.Surface(
                (self.config.train_width, self.config.train_height), pygame.SRCALPHA
            )

            # Draw train rectangle on surface
            pygame.draw.rect(
                train_surface,
                color,
                (0, 0, self.config.train_width, self.config.train_height),
            )
            pygame.draw.rect(
                train_surface,
                (0, 0, 0),
                (0, 0, self.config.train_width, self.config.train_height),
                1,
            )  # Border

            # Draw load indicator on surface
            if train_pos["capacity"] > 0:
                load_width = int(self.config.train_width * train_pos["load_factor"])
                # Color based on load factor
                if train_pos["load_factor"] < 0.5:
                    load_color = (0, 255, 0)  # Green
                elif train_pos["load_factor"] < 0.8:
                    load_color = (255, 255, 0)  # Yellow
                else:
                    load_color = (255, 0, 0)  # Red
                pygame.draw.rect(
                    train_surface,
                    load_color,
                    (0, 0, load_width, self.config.train_height),
                )

            # Rotate the train surface
            # Note: pygame rotation is counter-clockwise, and we need to negate
            # our angle because screen coordinates have Y increasing downward
            rotated_surface = pygame.transform.rotate(train_surface, -angle)

            # Get the rect of the rotated surface and center it on the position
            rotated_rect = rotated_surface.get_rect(center=(screen_x, screen_y))

            # Blit the rotated surface
            self.screen.blit(rotated_surface, rotated_rect)

    def _draw_ui(self):
        """Draw UI elements (title, stats, controls)."""
        # Title
        title = self.title_font.render(
            "Public Transport Simulation", True, self.text_color
        )
        self.screen.blit(title, (10, 10))

        # Simulation stats
        stats = self.simulator.get_statistics()
        time_text = f"Time: {stats['time']:.1f}s"
        trains_text = f"Trains: {stats['num_trains']}"
        lines_text = f"Lines: {', '.join(self.simulator.lines.keys())}"

        y_offset = 35
        for text_str in [time_text, trains_text, lines_text]:
            text = self.title_font.render(text_str, True, self.text_color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 20

        # Controls help
        if self.config.show_debug_info:
            fps_text = self.font.render(
                f"FPS: {self.clock.get_fps():.0f}", True, self.text_color
            )
            self.screen.blit(fps_text, (self.config.window_width - 100, 10))

            controls = [
                "SPACE: Pause/Resume",
                "R: Reset",
                "Q/ESC: Quit",
            ]
            y_offset = self.config.window_height - 60
            for control in controls:
                text = self.font.render(control, True, self.text_color)
                self.screen.blit(text, (10, y_offset))
                y_offset += 15

        # Paused indicator
        if self.paused:
            paused_text = self.title_font.render("PAUSED", True, (255, 0, 0))
            text_rect = paused_text.get_rect(center=(self.config.window_width // 2, 30))
            self.screen.blit(paused_text, text_rect)

    def _handle_events(self):
        """Handle Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.simulator.reset()
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    self.running = False

    def run(self):
        """Main visualization loop."""
        while self.running:
            # Handle events
            self._handle_events()

            # Update simulation (if not paused)
            if not self.paused:
                for _ in range(int(self.simulator.config.simulation_speed)):
                    self.simulator.step()

            # Clear screen
            self.screen.fill(self.bg_color)

            # Draw everything
            self._draw_lines()
            self._draw_stations()
            self._draw_passengers_at_station()
            self._draw_trains()
            self._draw_ui()

            # Update display
            pygame.display.flip()

            # Control FPS
            self.clock.tick(self.config.fps)

        # Cleanup
        pygame.quit()

    def __del__(self):
        """Cleanup on deletion."""
        try:
            pygame.quit()
        except:
            pass
