"""Export detected polygons to GeoJSON in real-world (lat/lng) coordinates."""
from __future__ import annotations

import json

from shapely.geometry import Polygon

from .geo import GeoReference


def polygon_to_geo_ring(poly: Polygon, georef: GeoReference) -> list[list[float]]:
    """Pixel polygon exterior -> GeoJSON ring of [lng, lat] pairs (closed)."""
    ring = []
    for x, y in poly.exterior.coords:
        lat, lng = georef.pixel_to_latlng(x, y)
        ring.append([lng, lat])  # GeoJSON is [lng, lat]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def to_geojson(
    polygons: list[Polygon],
    georef: GeoReference,
    properties: list[dict] | None = None,
) -> dict:
    """Build a GeoJSON FeatureCollection with per-building area in m²."""
    mpp = georef.meters_per_pixel()
    features = []
    for i, poly in enumerate(polygons):
        props = dict(properties[i]) if properties and i < len(properties) else {}
        props.setdefault("id", i + 1)
        props.setdefault("area_m2", round(poly.area * mpp * mpp, 1))
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_to_geo_ring(poly, georef)],
            },
            "properties": props,
        })
    return {"type": "FeatureCollection", "features": features}


def save_geojson(geojson: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(geojson, f, indent=2)
