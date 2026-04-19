"""
Configuration classes using Pydantic for validation.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SimulationConfig(BaseModel):
    """Main simulation configuration with validation."""

    ubahn_lines: list[str] = Field(
        default=["U8"],
        description="List of U-Bahn lines to simulate (e.g., ['U8', 'U1'])",
    )
    simulation_speed: float = Field(
        default=10.0, gt=0, le=1000, description="Simulation speed multiplier"
    )
    time_step_seconds: float = Field(
        default=1.0, gt=0, le=60, description="Simulation time step in seconds"
    )
    train_speed_kmh: float = Field(
        default=30.0, gt=0, le=100, description="Default train speed in km/h"
    )
    dwell_time_seconds: float = Field(
        default=20.0, ge=0, description="Base dwell time at stations in seconds"
    )
    trains_per_line: int = Field(
        default=1, ge=1, le=20, description="Number of trains per line"
    )
    gtfs_path: str = Field(default="GTFS/", description="Path to GTFS data directory")

    initial_passengers: int = Field(
        default=0, ge=0, le=1e5, description="Number of initial passengers to spawn"
    )

    model_config = {"frozen": True}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SimulationConfig":
        """Load configuration from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path):
        """Save configuration to a YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)


class VisualizationConfig(BaseModel):
    """Pygame visualization configuration with validation."""

    window_width: int = Field(
        default=1400, ge=800, le=3840, description="Window width in pixels"
    )
    window_height: int = Field(
        default=1000, ge=600, le=2160, description="Window height in pixels"
    )
    fps: int = Field(default=60, ge=10, le=120, description="Target frames per second")
    train_width: int = Field(
        default=15, ge=5, le=50, description="Train rectangle width"
    )
    train_height: int = Field(
        default=8, ge=3, le=30, description="Train rectangle height"
    )
    station_radius: int = Field(
        default=8, ge=3, le=20, description="Station circle radius"
    )
    show_station_names: bool = Field(
        default=True, description="Show station names on map"
    )
    show_debug_info: bool = Field(
        default=True, description="Show FPS and simulation info"
    )

    # Colors (hex codes)
    background_color: str = Field(default="#FFFFFF", description="Background color")
    station_color: str = Field(default="#000000", description="Station color")
    train_color: str = Field(default="#FF0000", description="Default train color")
    text_color: str = Field(default="#000000", description="Text color")

    model_config = {"frozen": True}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "VisualizationConfig":
        """Load configuration from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path):
        """Save configuration to a YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)


class Config(BaseModel):
    """Combined configuration for simulation and visualization."""

    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)

    model_config = {"frozen": True}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """Load combined configuration from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path):
        """Save combined configuration to a YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
