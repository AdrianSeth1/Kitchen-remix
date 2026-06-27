"""
FLUX.1 Kontext [dev] inference wrapper.

NOTE: Pipeline class names are verified against diffusers at load time.
Before adding model-loading code here, run:
  python -c "from diffusers import FluxKontextPipeline; print('ok')"
and check https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev
for the current recommended load pattern.

This module is intentionally left as a stub for Phase 0.
Phase 1 will fill in load_pipeline() and edit_image().
"""
from __future__ import annotations

import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

_pipeline = None  # module-level singleton; loaded once at startup


def load_pipeline() -> None:
    """Load the Kontext pipeline into VRAM. Called once from lifespan."""
    global _pipeline
    if _pipeline is not None:
        return

    # Phase 1: verify diffusers API, then implement.
    # Example (not final — verify class name before using):
    #   from diffusers import FluxKontextPipeline
    #   _pipeline = FluxKontextPipeline.from_pretrained(
    #       config.KONTEXT_MODEL_ID,
    #       torch_dtype=torch.float8_e4m3fn,
    #       token=config.HF_TOKEN,
    #       cache_dir=config.MODELS_DIR,
    #   ).to("cuda")
    logger.warning("pipeline.py: model loading not yet implemented (Phase 1 stub)")


def is_loaded() -> bool:
    return _pipeline is not None


def edit_image(image: Image.Image, instruction: str, seed: int) -> Image.Image:
    """
    Apply instruction to image and return the edited PIL image.
    Raises RuntimeError if the pipeline is not loaded.
    """
    if _pipeline is None:
        raise RuntimeError("Pipeline not loaded. Call load_pipeline() first.")

    # Phase 1 implementation goes here.
    raise NotImplementedError("edit_image() not yet implemented (Phase 1 stub)")
