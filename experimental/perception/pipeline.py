"""End-to-end orchestration of the building perception stack.

    acquire -> segment -> polygonize -> visualize / export

Each stage is independently swappable; ``PerceptionPipeline`` just wires them
together and carries the GeoReference through so results land in real-world
coordinates.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import Polygon

from . import acquisition, export, polygonize, visualize
from .geo import GeoReference
from .segmentation import BuildingSegmenter


@dataclass
class PerceptionResult:
    image: np.ndarray
    georef: GeoReference
    masks: list[np.ndarray]
    polygons: list[Polygon]            # pixel space
    annotated: np.ndarray
    geojson: dict = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.polygons)


@dataclass
class PerceptionPipeline:
    segmenter: BuildingSegmenter
    min_area_px: float = 200.0
    simplify_tol: float = 2.0
    regularize: bool = True

    def run(self, image: np.ndarray, georef: GeoReference) -> PerceptionResult:
        """Run inference + vectorization + rendering on an in-memory image."""
        masks = self.segmenter.segment(image)
        polygons = polygonize.polygons_from_masks(
            masks,
            min_area_px=self.min_area_px,
            simplify_tol=self.simplify_tol,
            regularize=self.regularize,
        )
        annotated = visualize.draw_polygons(image, polygons)
        geojson = export.to_geojson(polygons, georef)
        return PerceptionResult(image, georef, masks, polygons, annotated, geojson)

    def run_from_coords(
        self,
        lat: float,
        lng: float,
        zoom: int = 19,
        api_key: str | None = None,
        mosaic: tuple[int, int] | None = None,
        **fetch_kw,
    ) -> PerceptionResult:
        """Fetch imagery from Google Static Maps, then run the stack."""
        api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
        if mosaic:
            cols, rows = mosaic
            image, georef = acquisition.fetch_mosaic(
                lat, lng, zoom=zoom, cols=cols, rows=rows, api_key=api_key, **fetch_kw)
        else:
            image, georef = acquisition.fetch_satellite(
                lat, lng, zoom=zoom, api_key=api_key, **fetch_kw)
        return self.run(image, georef)
