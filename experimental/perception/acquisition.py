"""Imagery acquisition from the Google Maps Static API.

Uses the official Static Maps endpoint (`maptype=satellite`). This requires a
Google Maps Platform API key and is subject to Google's Terms of Service —
notably, satellite imagery may not be scraped or stored outside the allowances
of the ToS. Use this for analysis/prototyping in line with those terms.
"""
from __future__ import annotations

import io

import numpy as np
import requests
from PIL import Image

from .geo import GeoReference, latlng_to_norm, norm_to_latlng

STATIC_MAPS_URL = "https://maps.googleapis.com/maps/api/staticmap"
# Google overlays a ~22px logical-pixel attribution band at the bottom.
LOGO_BAND_PX = 22


def fetch_satellite(
    lat: float,
    lng: float,
    zoom: int = 19,
    size: tuple[int, int] = (640, 640),
    scale: int = 2,
    api_key: str | None = None,
    crop_logo: bool = True,
    session: requests.Session | None = None,
) -> tuple[np.ndarray, GeoReference]:
    """Fetch a single satellite tile centered on (lat, lng).

    Returns an (H, W, 3) uint8 RGB array and its GeoReference. `size` is the
    logical size (max 640 per side without a premium plan); `scale` of 2
    doubles pixel resolution for the same ground footprint.
    """
    if not api_key:
        raise ValueError(
            "A Google Maps Platform API key is required. Pass api_key=... or set "
            "the GOOGLE_MAPS_API_KEY environment variable."
        )
    w, h = size
    params = {
        "center": f"{lat},{lng}",
        "zoom": zoom,
        "size": f"{w}x{h}",
        "scale": scale,
        "maptype": "satellite",
        "format": "png",
        "key": api_key,
    }
    http = session or requests
    resp = http.get(STATIC_MAPS_URL, params=params, timeout=30)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    arr = np.asarray(img)

    logical_h = h
    if crop_logo:
        crop_px = LOGO_BAND_PX * scale
        arr = arr[: arr.shape[0] - crop_px, :, :]
        logical_h = h - LOGO_BAND_PX

    georef = GeoReference(lat, lng, zoom, w, logical_h, scale)
    return np.ascontiguousarray(arr), georef


def fetch_mosaic(
    lat: float,
    lng: float,
    zoom: int = 19,
    cols: int = 2,
    rows: int = 2,
    tile_size: tuple[int, int] = (640, 640),
    scale: int = 2,
    api_key: str | None = None,
    session: requests.Session | None = None,
) -> tuple[np.ndarray, GeoReference]:
    """Stitch a `cols` x `rows` grid of tiles into one georeferenced mosaic.

    Each cell is fetched at its own computed center (logo cropped) and pasted
    onto a single canvas. Returns the mosaic and a GeoReference covering the
    whole region.
    """
    tw, th = tile_size
    th_cropped = th - LOGO_BAND_PX
    world = 256 * (2 ** zoom)
    cnx, cny = latlng_to_norm(lat, lng)
    cwx, cwy = cnx * world, cny * world

    region_w, region_h = cols * tw, rows * th_cropped
    top_left_wx = cwx - region_w / 2.0
    top_left_wy = cwy - region_h / 2.0

    canvas = np.zeros((region_h * scale, region_w * scale, 3), dtype=np.uint8)
    http = session or requests.Session()

    for i in range(rows):
        for j in range(cols):
            cell_wx = top_left_wx + (j + 0.5) * tw
            cell_wy = top_left_wy + (i + 0.5) * th_cropped + LOGO_BAND_PX / 2.0
            cell_lat, cell_lng = norm_to_latlng(cell_wx / world, cell_wy / world)
            tile, _ = fetch_satellite(
                cell_lat, cell_lng, zoom=zoom, size=tile_size, scale=scale,
                api_key=api_key, crop_logo=True, session=http,
            )
            y0, x0 = i * th_cropped * scale, j * tw * scale
            canvas[y0:y0 + tile.shape[0], x0:x0 + tile.shape[1]] = tile

    region_lat, region_lng = norm_to_latlng(
        (top_left_wx + region_w / 2.0) / world,
        (top_left_wy + region_h / 2.0) / world,
    )
    georef = GeoReference(region_lat, region_lng, zoom, region_w, region_h, scale)
    return canvas, georef
