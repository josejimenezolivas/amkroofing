"""Web Mercator georeferencing for Google Static Maps imagery.

Google's static maps use the standard Web Mercator (EPSG:3857) projection on a
256px tile grid. Given the center lat/lng, zoom, logical size and scale of a
fetched image, this module maps any output pixel back to (lat, lng) and vice
versa, so segmentation results in pixel space can be lifted to real-world
geographic coordinates.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

TILE_SIZE = 256
# Latitude limits of the Web Mercator projection.
MAX_LAT = 85.05112878


def latlng_to_norm(lat: float, lng: float) -> tuple[float, float]:
    """Lat/lng -> normalized [0, 1] Web Mercator coordinates (origin top-left)."""
    lat = max(min(lat, MAX_LAT), -MAX_LAT)
    nx = (lng + 180.0) / 360.0
    lat_rad = math.radians(lat)
    ny = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0
    return nx, ny


def norm_to_latlng(nx: float, ny: float) -> tuple[float, float]:
    """Normalized [0, 1] Web Mercator coordinates -> (lat, lng)."""
    lng = nx * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * ny)))
    return math.degrees(lat_rad), lng


@dataclass
class GeoReference:
    """Georeferencing metadata tying an output image to the ground.

    `width`/`height` are *logical* pixels (what you pass to Google as `size`).
    `scale` is the static-maps scale factor (1 or 2); the actual returned image
    is `width*scale` x `height*scale` pixels but covers the same ground area.
    """

    center_lat: float
    center_lng: float
    zoom: int
    width: int
    height: int
    scale: int = 1

    @property
    def world_size(self) -> float:
        """Size of the full world, in pixels, at this zoom level."""
        return TILE_SIZE * (2 ** self.zoom)

    def _center_world(self) -> tuple[float, float]:
        cnx, cny = latlng_to_norm(self.center_lat, self.center_lng)
        return cnx * self.world_size, cny * self.world_size

    def pixel_to_latlng(self, px: float, py: float) -> tuple[float, float]:
        """Output-image pixel (already scaled) -> (lat, lng)."""
        cwx, cwy = self._center_world()
        lx, ly = px / self.scale, py / self.scale
        wx = cwx - self.width / 2.0 + lx
        wy = cwy - self.height / 2.0 + ly
        return norm_to_latlng(wx / self.world_size, wy / self.world_size)

    def bounds(self) -> tuple[float, float, float, float]:
        """(south, west, north, east) of the image footprint."""
        north, west = self.pixel_to_latlng(0, 0)
        south, east = self.pixel_to_latlng(self.width * self.scale, self.height * self.scale)
        return south, west, north, east

    def meters_per_pixel(self) -> float:
        """Ground resolution of one *output* pixel at the center latitude."""
        return (156543.03392 * math.cos(math.radians(self.center_lat))
                / (2 ** self.zoom) / self.scale)
