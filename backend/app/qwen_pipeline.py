"""
Qwen-Image-Edit-2509 inference wrapper (Tier B — object reference / replacement).

API verified 2026-06 against:
  https://huggingface.co/Qwen/Qwen-Image-Edit-2509
  https://huggingface.co/docs/diffusers/main/api/pipelines/qwenimage

The 2509 multi-image model uses QwenImageEditPlusPipeline. Multiple images are
passed as a LIST in the single `image=` argument (first = kitchen, rest = refs);
there is no separate `images=` parameter.

Memory: this model is ~20GB+ in bf16 and cannot be co-resident with Kontext on a
24GB card. backends.ensure() unloads the other model first; unload() here frees
the VRAM so the next model can load.
"""
from __future__ import annotations

import logging
from PIL import Image

from . import config

# torch is imported lazily inside load_pipeline() / edit_with_references() so the
# server can boot on a machine without the ML stack. Do not add a top-level
# `import torch`.

logger = logging.getLogger(__name__)

_pipeline = None  # module-level singleton; loaded on demand


def load_pipeline() -> None:
    """Load QwenImageEditPlusPipeline into VRAM. Safe to call multiple times."""
    global _pipeline
    if _pipeline is not None:
        return

    try:
        import torch
    except ImportError:
        logger.warning(
            "torch not installed — Qwen model will not load. "
            "Install PyTorch (see requirements.txt) then restart the server."
        )
        return

    logger.info("Importing diffusers …")
    try:
        from diffusers import QwenImageEditPlusPipeline
    except ImportError:
        logger.warning(
            "diffusers not installed (or too old for QwenImageEditPlusPipeline). "
            "Run: pip install git+https://github.com/huggingface/diffusers.git"
        )
        return

    logger.info("Loading %s (bfloat16) …", config.QWEN_MODEL_ID)
    pipe = QwenImageEditPlusPipeline.from_pretrained(
        config.QWEN_MODEL_ID,
        torch_dtype=torch.bfloat16,
        token=config.HF_TOKEN or None,
        cache_dir=str(config.MODELS_DIR),
    )

    # Offload text encoders to CPU RAM between ops; transformer stays in VRAM.
    pipe.enable_model_cpu_offload()

    _pipeline = pipe
    logger.info("Qwen pipeline ready.")


def is_loaded() -> bool:
    return _pipeline is not None


def unload() -> None:
    """Drop the pipeline and free its VRAM so the other model can load."""
    global _pipeline
    if _pipeline is None:
        return
    _pipeline = None
    try:
        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass
    logger.info("Qwen pipeline unloaded.")


def edit_with_references(
    image: Image.Image, refs: list[Image.Image], instruction: str, seed: int
) -> Image.Image:
    """
    Replace/insert using reference images. `image` is the kitchen; `refs` are the
    reference photo(s). QwenImageEditPlusPipeline takes them as one list.

    Same seed → same output, for reproducibility.
    """
    if _pipeline is None:
        raise RuntimeError("Qwen pipeline not loaded. Call load_pipeline() first.")
    if not refs:
        raise ValueError("At least one reference image must be provided")

    import torch
    generator = torch.Generator("cpu").manual_seed(seed)

    result = _pipeline(
        image=[image, *refs],
        prompt=instruction,
        guidance_scale=config.QWEN_GUIDANCE_SCALE,
        num_inference_steps=config.QWEN_NUM_INFERENCE_STEPS,
        generator=generator,
    )

    return result.images[0]
