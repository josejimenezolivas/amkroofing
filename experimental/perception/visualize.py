"""Render detected building polygons onto the source image."""
from __future__ import annotations

import cv2
import numpy as np
from shapely.geometry import Polygon


def draw_polygons(
    image: np.ndarray,
    polygons: list[Polygon],
    color: tuple[int, int, int] = (255, 90, 60),
    fill_alpha: float = 0.30,
    thickness: int = 2,
    label: bool = True,
) -> np.ndarray:
    """Return a copy of `image` with polygons filled, outlined and numbered."""
    out = image.copy()
    overlay = image.copy()
    for poly in polygons:
        pts = np.array(poly.exterior.coords, dtype=np.int32)
        cv2.fillPoly(overlay, [pts], color)
    cv2.addWeighted(overlay, fill_alpha, out, 1 - fill_alpha, 0, out)

    for idx, poly in enumerate(polygons, start=1):
        pts = np.array(poly.exterior.coords, dtype=np.int32)
        cv2.polylines(out, [pts], isClosed=True, color=color, thickness=thickness,
                      lineType=cv2.LINE_AA)
        if label:
            cx, cy = poly.centroid.coords[0]
            _label(out, str(idx), int(cx), int(cy))
    return out


def _label(img: np.ndarray, text: str, x: int, y: int) -> None:
    font, fs, th = cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
    (tw, tht), _ = cv2.getTextSize(text, font, fs, th)
    cv2.rectangle(img, (x - tw // 2 - 3, y - tht // 2 - 3),
                  (x + tw // 2 + 3, y + tht // 2 + 3), (0, 0, 0), -1)
    cv2.putText(img, text, (x - tw // 2, y + tht // 2), font, fs,
                (255, 255, 255), th, cv2.LINE_AA)
