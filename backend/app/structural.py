"""
Structural / experimental edit helpers.

Remove (reliable), Move, and Open-wall (both experimental — approximate geometry).
Phase 3.5 stub. Actual implementation goes here after Phase 2 is complete.
"""
from __future__ import annotations

from PIL import Image
from . import pipeline


def remove_object(image: Image.Image, target: str, seed: int) -> Image.Image:
    """Remove a named object and rebuild the surface behind it."""
    instruction = (
        f"Remove the {target} and fill the space with matching wall and flooring. "
        "Keep everything else in the kitchen unchanged."
    )
    return pipeline.edit_image(image, instruction, seed)


def move_object(
    image: Image.Image, target: str, destination: str, seed: int
) -> Image.Image:
    """
    Move an object to a new location.
    Implemented as remove-then-add; placement is approximate.
    """
    step1 = remove_object(image, target, seed)
    instruction = (
        f"Add a {target} at {destination}. "
        "Keep everything else in the kitchen unchanged."
    )
    return pipeline.edit_image(step1, instruction, seed)


def open_wall(
    image: Image.Image, wall_description: str, seed: int
) -> Image.Image:
    """
    Open or remove a wall. The space beyond is invented — not accurate.
    """
    instruction = (
        f"Remove {wall_description} and open the kitchen to the adjacent room. "
        "Keep all other walls, cabinets, and surfaces unchanged."
    )
    return pipeline.edit_image(image, instruction, seed)
