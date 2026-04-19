"""
Main entry point for the public transport simulation.
"""

import sys
from pathlib import Path

from src.core.config import Config
from src.simulation.simulator import Simulator
from src.visualization.pygame_visualizer import PygameVisualizer


def main():
    """Run the public transport simulation with visualization."""
    # Load configuration
    config_path = Path("config.yaml")
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        print("Creating default configuration...")
        config = Config()
        config.to_yaml(config_path)
        print(f"Default configuration saved to {config_path}")
        print("Please edit the configuration and run again.")
        return 1

    print(f"Loading configuration from {config_path}...")
    config = Config.from_yaml(config_path)

    # Validate GTFS path
    gtfs_path = Path(config.simulation.gtfs_path)
    if not gtfs_path.exists():
        print(f"Error: GTFS data directory not found at {gtfs_path}")
        print("Please download GTFS data and update config.yaml")
        return 1

    print(f"GTFS path: {gtfs_path}")

    # Initialize simulator
    print("\nInitializing simulator...")
    try:
        simulator = Simulator(config.simulation)
    except Exception as e:
        print(f"Error initializing simulator: {e}")
        return 1

    if len(simulator.lines) == 0:
        print("Error: No lines loaded. Check GTFS data and configuration.")
        return 1

    print(f"Loaded {len(simulator.lines)} line(s):")
    for line in simulator.lines.values():
        print(f"  - {line}")

    # Initialize visualizer
    print("\nInitializing visualizer...")
    visualizer = PygameVisualizer(simulator, config.visualization)

    # Run simulation
    print("\nStarting simulation...")
    print("Controls:")
    print("  SPACE: Pause/Resume")
    print("  R: Reset simulation")
    print("  Q/ESC: Quit")
    print()

    try:
        visualizer.run()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
    except Exception as e:
        print(f"\nError during simulation: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("Simulation ended.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
