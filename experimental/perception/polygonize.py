"""Vectorization: turn raster instance masks into clean building polygons.

Raw segmentation masks have ragged, pixel-stepped boundaries. Buildings, in
contrast, are dominated by straight edges and right angles. This stage:

  1. traces external contours,
  2. drops specks below a minimum area,
  3. simplifies with Douglas-Peucker,
  4. optionally "regularizes" near-rectangular footprints to their minimum-area
     rotated rectangle for crisp, map-ready outlines.

Polygons are returned in pixel space (shapely Polygons, x=col, y=row).
"""
from __future__ import annotations

import cv2
import numpy as np
from shapely.geometry import MultiPolygon, Polygon


def mask_to_polygons(
    mask: np.ndarray,
    min_area_px: float = 200.0,
    simplify_tol: float = 2.0,
    regularize: bool = True,
    rect_fill_ratio: float = 0.85,
) -> list[Polygon]:
    """Convert one instance mask into one or more simplified polygons."""
    m = (mask > 0).astype(np.uint8)
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polys: list[Polygon] = []
    for contour in contours:
        if cv2.contourArea(contour) < min_area_px:
            continue
        approx = cv2.approxPolyDP(contour, simplify_tol, True).reshape(-1, 2)
        if len(approx) < 3:
            continue
        poly = Polygon(approx)
        if not poly.is_valid:
            poly = poly.buffer(0)  # may split into a MultiPolygon
        for part in _iter_polygons(poly):
            if part.is_empty or part.area < min_area_px:
                continue
            if regularize:
                part = _regularize(contour, part, rect_fill_ratio)
            polys.append(part)
    return polys


def _iter_polygons(geom):
    """Yield Polygon parts from a Polygon or MultiPolygon (skip other types)."""
    if isinstance(geom, Polygon):
        yield geom
    elif isinstance(geom, MultiPolygon):
        yield from geom.geoms


def _regularize(contour: np.ndarray, poly: Polygon, rect_fill_ratio: float) -> Polygon:
    """Snap to a rotated rectangle when the footprint is essentially boxy."""
    (cx, cy), (w, h), angle = cv2.minAreaRect(contour)
    rect_area = w * h
    if rect_area <= 0:
        return poly
    if poly.area / rect_area >= rect_fill_ratio:
        box = cv2.boxPoints(((cx, cy), (w, h), angle))
        return Polygon(box)
    return poly


def polygons_from_masks(masks: list[np.ndarray], **kw) -> list[Polygon]:
    """Flatten a list of instance masks into a single list of polygons."""
    out: list[Polygon] = []
    for mask in masks:
        out.extend(mask_to_polygons(mask, **kw))
    return out
