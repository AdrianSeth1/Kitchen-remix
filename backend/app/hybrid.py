"""
Phase 5 stretch: geometry-controlled rendering via ControlNet.

The user supplies a geometry control (depth map, canny edge image, or
rendered blockout). A ControlNet-conditioned pipeline imposes correct
scale and perspective, then Kontext-style prompting handles surfaces
and materials.

Verify current ControlNet options against diffusers docs before implementing.
This file is a sketch — do not wire into routes until Phase 5.
"""
from __future__ import annotations

from PIL import Image


def geometry_edit(
    image: Image.Image,
    control_image: Image.Image,
    instruction: str,
    seed: int,
) -> Image.Image:
    """
    Geometry-controlled edit (Phase 5 stretch).
    control_image: depth map, canny, or segmentation mask from user-supplied layout.
    """
    raise NotImplementedError("hybrid.py: Phase 5 sketch, not yet implemented.")
