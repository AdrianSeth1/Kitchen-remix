"""
Structural / experimental edit helpers.

Remove (reliable), Move, and Open-wall (both experimental — approximate geometry).

Instruction wording is the single source of truth in structural.json — these
helpers load the first template for each action and fill in the placeholders.
Keeping the phrasing in the JSON means the curated wording and the UI caveats
live in one place and can't drift from the code.
"""
from __future__ import annotations

import json
from functools import lru_cache

from PIL import Image
from . import config, pipeline


@lru_cache(maxsize=1)
def _templates() -> dict:
    """Load and cache structural.json. Cache is process-lifetime."""
    return json.loads(config.STRUCTURAL_JSON.read_text(encoding="utf-8"))


def remove_object(image: Image.Image, target: str, seed: int) -> Image.Image:
    """Remove a named object and rebuild the surface behind it."""
    instruction = _templates()["remove_templates"][0].format(target=target)
    return pipeline.edit_image(image, instruction, seed)


def move_object(
    image: Image.Image, target: str, destination: str, seed: int
) -> Image.Image:
    """
    Move an object to a new location in a single pass. Placement is approximate.

    The curated move template already tells the model to rebuild the old
    location, so a single edit is cleaner than a remove-then-add chain (one
    inference pass, fewer compounding artifacts).
    """
    instruction = _templates()["move_templates"][0].format(
        target=target, destination=destination
    )
    return pipeline.edit_image(image, instruction, seed)


def open_wall(
    image: Image.Image, wall_description: str, seed: int
) -> Image.Image:
    """
    Open or remove a wall. The space beyond is invented — not accurate.
    """
    instruction = _templates()["open_wall_templates"][0].format(
        wall_description=wall_description
    )
    return pipeline.edit_image(image, instruction, seed)
