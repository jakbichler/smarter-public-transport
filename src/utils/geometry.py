"""Geometry utilities for geographic calculations"""

import numpy as np


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    # Radius of Earth in kilometers
    r = 6371.0

    return c * r


def interpolate_position(
    lat1: float, lon1: float, lat2: float, lon2: float, progress: float
) -> tuple[float, float]:
    """
    Linearly interpolate between two geographic positions.

    Args:
        lat1: Latitude of first point (degrees)
        lon1: Longitude of first point (degrees)
        lat2: Latitude of second point (degrees)
        lon2: Longitude of second point (degrees)
        progress: Interpolation factor (0.0 to 1.0)

    Returns:
        Tuple of (latitude, longitude) at the interpolated position
    """
    lat = lat1 + progress * (lat2 - lat1)
    lon = lon1 + progress * (lon2 - lon1)
    return lat, lon
