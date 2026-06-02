# Satellite Building Perception Stack

A modular perception pipeline that pulls satellite imagery from Google Maps and
returns building footprints as both an annotated image and georeferenced
GeoJSON.

```
acquire ──▶ segment ──▶ polygonize ──▶ visualize
(Static    (SAM /       (contours,      (overlay)
 Maps)      classical)   simplify,    ──▶ export
                         regularize)      (GeoJSON, lat/lng + m²)
```

Each stage is an independent, swappable component; `PerceptionPipeline` wires
them together and threads a `GeoReference` through so pixel-space results are
lifted to real-world coordinates.

## Modules

| File | Stage | Responsibility |
|------|-------|----------------|
| `geo.py` | — | Web Mercator math; pixel ↔ lat/lng, bounds, m/px |
| `acquisition.py` | acquire | Google Static Maps fetch + multi-tile mosaic |
| `segmentation.py` | segment | Pluggable backends (SAM / classical / precomputed) |
| `polygonize.py` | polygonize | Mask → contours → Douglas-Peucker → rectangle regularization |
| `visualize.py` | visualize | Translucent fills, outlines, numbered labels |
| `export.py` | export | GeoJSON FeatureCollection with per-building area in m² |
| `pipeline.py` | — | Orchestrator + `run_from_coords()` convenience |

## Setup

```bash
pip install -r requirements.txt
# For the production SAM backend:
pip install segment-geospatial torch torchvision
```

## Usage

```python
from satellite_perception import PerceptionPipeline, SAMSegmenter

pipe = PerceptionPipeline(
    SAMSegmenter(mode="text", text_prompt="building"),  # building-specific
    min_area_px=300, regularize=True,
)
res = pipe.run_from_coords(37.4220, -122.0841, zoom=19,
                           api_key="YOUR_GOOGLE_MAPS_KEY")

print(res.count)               # number of buildings
res.annotated                  # RGB ndarray with polygons drawn
res.geojson                    # FeatureCollection in lat/lng
```

Quick offline demo (no key / GPU, synthetic scene):

```bash
python example.py --demo
```

## Segmentation backends

- **`SAMSegmenter`** — production. Wraps [`segment-geospatial`](https://github.com/opengeos/segment-geospatial)
  (Segment Anything). `mode="text"` uses LangSAM to segment only what matches a
  text prompt ("building"); `mode="auto"` generates all masks then filters by
  area. Lazy-imported, so the rest of the package runs without torch.
- **`ClassicalSegmenter`** — dependency-light CV heuristic. Exercises the full
  stack with no model; **not accurate enough for real mapping**.
- **`PrecomputedSegmenter`** — wraps masks you already have (another model, or
  for unit-testing the downstream stages).

Swap in any detector by implementing one method:

```python
class MySegmenter:
    def segment(self, image_rgb) -> list[np.ndarray]:  # list of bool masks
        ...
```

## Polygon regularization

Raw masks give ragged, pixel-stepped outlines. The polygonizer simplifies with
Douglas-Peucker and, when a footprint nearly fills its minimum-area rotated
rectangle (`rect_fill_ratio`), snaps it to that rectangle for crisp, map-ready
building outlines. Disable with `regularize=False` for organic/complex shapes.

## Georeferencing

`GeoReference` implements the standard 256px-tile Web Mercator projection, so
any output pixel maps back to lat/lng. Bounds, ground resolution (`m/px`), and
GeoJSON coordinates are all derived from the fetch parameters (center, zoom,
size, scale). The Google attribution band is cropped before inference and the
logical height adjusted so georeferencing stays exact.

## A note on Google's Terms of Service

This uses the official Google Maps Platform **Static Maps API** and requires
your own API key. Satellite imagery from Google is subject to the Google Maps
Platform Terms of Service, which restrict caching, bulk downloading, and
redistribution. Use within those terms. For permissively-licensed alternatives,
consider open building datasets (e.g. Google Open Buildings, Microsoft Building
Footprints) or open imagery sources, which `acquisition.py` can be adapted to.
```
