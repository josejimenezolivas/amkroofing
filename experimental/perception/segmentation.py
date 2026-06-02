"""Building segmentation backends.

The pipeline treats segmentation as a pluggable stage that consumes an RGB
image and produces a list of per-instance boolean masks. Three backends ship:

* ``SAMSegmenter``        - production quality, wraps `segment-geospatial`
                            (Segment Anything). Lazy-imported so the rest of the
                            package works without torch installed.
* ``ClassicalSegmenter``  - dependency-light CV heuristic. Useful for smoke
                            tests / no-GPU demos; NOT production accurate.
* ``PrecomputedSegmenter``- wraps masks you already have (e.g. from another
                            model or for unit testing the downstream stack).
"""
from __future__ import annotations

from typing import Protocol

import cv2
import numpy as np


class BuildingSegmenter(Protocol):
    """Anything with ``segment(image) -> list[bool mask]`` is a valid backend."""

    def segment(self, image: np.ndarray) -> list[np.ndarray]:
        ...


class PrecomputedSegmenter:
    """Return masks supplied at construction time. Handy for tests/integration."""

    def __init__(self, masks: list[np.ndarray]):
        self._masks = [m.astype(bool) for m in masks]

    def segment(self, image: np.ndarray) -> list[np.ndarray]:
        return self._masks


class SAMSegmenter:
    """Segment Anything backend via `segment-geospatial` (samgeo).

    Two modes:
      * mode="text"  -> text-prompted (LangSAM): only segments instances
                        matching ``text_prompt`` (default "building"). Best for
                        building-specific extraction. Requires GroundingDINO.
      * mode="auto"  -> automatic mask generation, then optionally filter masks
                        by area to drop obvious non-buildings.

    Install: ``pip install segment-geospatial torch torchvision``.
    """

    def __init__(
        self,
        mode: str = "text",
        text_prompt: str = "building",
        box_threshold: float = 0.24,
        text_threshold: float = 0.24,
        model_type: str = "vit_h",
        device: str | None = None,
    ):
        self.mode = mode
        self.text_prompt = text_prompt
        self.box_threshold = box_threshold
        self.text_threshold = text_threshold
        self.model_type = model_type
        self.device = device
        self._model = None  # lazily built on first use

    def _ensure_model(self):
        if self._model is not None:
            return
        if self.mode == "text":
            from samgeo.text_sam import LangSAM
            self._model = LangSAM()
        else:
            from samgeo import SamGeo
            self._model = SamGeo(model_type=self.model_type, device=self.device,
                                 sam_kwargs=None)

    def segment(self, image: np.ndarray) -> list[np.ndarray]:
        import tempfile, os
        self._ensure_model()
        # samgeo operates on files; round-trip through a temp PNG.
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "in.tif")
            cv2.imwrite(src, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
            if self.mode == "text":
                self._model.predict(src, self.text_prompt,
                                    box_threshold=self.box_threshold,
                                    text_threshold=self.text_threshold)
                # LangSAM exposes per-detection masks as (N, H, W).
                masks = np.asarray(self._model.masks)
                if masks.ndim == 2:
                    masks = masks[None]
                return [m.astype(bool) for m in masks]
            else:
                out = os.path.join(tmp, "mask.tif")
                self._model.generate(src, out)
                label = cv2.imread(out, cv2.IMREAD_UNCHANGED)
                return _split_label_image(label)


class ClassicalSegmenter:
    """Dependency-light heuristic blob detector (DEMO ONLY, not accurate).

    Suppresses vegetation (green-dominant) and roads, keeps compact bright/box
    regions, then returns connected components above ``min_area``. Good enough
    to exercise the full stack without a model; do not use for real mapping.
    """

    def __init__(self, min_area: int = 600):
        self.min_area = min_area

    def segment(self, image: np.ndarray) -> list[np.ndarray]:
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        vegetation = (h > 35) & (h < 95) & (s > 40)
        candidate = (~vegetation) & (v > 60)
        m = (candidate.astype(np.uint8)) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=1)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)
        return _split_label_image(cv2.connectedComponents(m)[1], self.min_area)


def _split_label_image(label: np.ndarray, min_area: int = 1) -> list[np.ndarray]:
    """Split an integer label image into a list of per-instance boolean masks."""
    masks = []
    for lbl in np.unique(label):
        if lbl == 0:
            continue
        mask = label == lbl
        if mask.sum() >= min_area:
            masks.append(mask)
    return masks
