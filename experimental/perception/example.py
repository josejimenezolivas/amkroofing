"""Example: detect building footprints over a coordinate from Google satellite.

Usage:
    export GOOGLE_MAPS_API_KEY="..."
    python example.py 37.4220 -122.0841

Without a key (offline demo on a synthetic scene):
    python example.py --demo
"""
from __future__ import annotations

import sys

import cv2
import numpy as np

from satellite_perception import (PerceptionPipeline, SAMSegmenter,
                                   ClassicalSegmenter, PrecomputedSegmenter,
                                   GeoReference)
from satellite_perception.export import save_geojson


def real(lat: float, lng: float):
    # mode="text" => building-specific extraction via LangSAM ("building").
    pipe = PerceptionPipeline(SAMSegmenter(mode="text", text_prompt="building"),
                              min_area_px=300, regularize=True)
    res = pipe.run_from_coords(lat, lng, zoom=19)  # reads GOOGLE_MAPS_API_KEY
    _save(res)


def demo():
    """Synthetic scene + ground-truth masks; no key/GPU needed."""
    g = GeoReference(37.4220, -122.0841, zoom=19, width=640, height=618, scale=2)
    H, W = 618 * 2, 640 * 2
    img = np.random.default_rng(7).normal(95, 12, (H, W, 3)).clip(0, 255).astype(np.uint8)
    masks = []
    for cx, cy, w, h, ang in [(300, 260, 220, 140, 18), (720, 400, 180, 260, -25),
                              (980, 820, 300, 180, 40)]:
        box = cv2.boxPoints(((cx, cy), (w, h), ang)).astype(np.int32)
        cv2.fillPoly(img, [box], (190, 180, 175))
        m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [box], 1)
        masks.append(m.astype(bool))
    pipe = PerceptionPipeline(PrecomputedSegmenter(masks), min_area_px=300)
    _save(pipe.run(img, g))


def _save(res):
    cv2.imwrite("buildings_annotated.png", cv2.cvtColor(res.annotated, cv2.COLOR_RGB2BGR))
    save_geojson(res.geojson, "buildings.geojson")
    print(f"Detected {res.count} buildings.")
    print("Wrote buildings_annotated.png and buildings.geojson")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    elif len(sys.argv) >= 3:
        real(float(sys.argv[1]), float(sys.argv[2]))
    else:
        print(__doc__)
