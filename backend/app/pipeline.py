"""
FLUX.1 Kontext [dev] inference wrapper.

API verified 2026-06 against:
  https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev
  https://huggingface.co/docs/diffusers/main/en/api/pipelines/flux

Requires diffusers from git main (not PyPI stable):
  pip install git+https://github.com/huggingface/diffusers.git

Memory strategy for RTX 4090 (24 GB):
  - bfloat16 throughout (the transformer alone is ~24 GB in bf16)
  - enable_model_cpu_offload() keeps the transformer in VRAM during inference
    while T5 and CLIP live in system RAM between forward passes
  - enable_vae_slicing() prevents VAE OOM on high-res outputs

If you still hit OOM, quantize the transformer to fp8 with optimum-quanto
(see README for the recipe) — cuts transformer VRAM to ~12 GB.
"""
from __future__ import annotations

import logging
from PIL import Image

from . import config

# torch is imported lazily inside load_pipeline() / edit_image() so the
# server can boot on a machine without the ML stack (e.g. CI or cold start
# before the model is installed).  Do not add a top-level `import torch`.

logger = logging.getLogger(__name__)

_pipeline = None  # module-level singleton; loaded once at startup


def load_pipeline() -> None:
    """Load FluxKontextPipeline into VRAM. Safe to call multiple times."""
    global _pipeline
    if _pipeline is not None:
        return

    try:
        import torch
    except ImportError:
        logger.warning(
            "torch not installed — model will not load. "
            "Install PyTorch (see requirements.txt) then restart the server."
        )
        return

    logger.info("Importing diffusers …")
    try:
        from diffusers import FluxKontextPipeline
    except ImportError:
        logger.warning(
            "diffusers not installed — model will not load. "
            "Run: pip install git+https://github.com/huggingface/diffusers.git"
        )
        return

    logger.info("Loading %s (bfloat16) …", config.KONTEXT_MODEL_ID)
    pipe = FluxKontextPipeline.from_pretrained(
        config.KONTEXT_MODEL_ID,
        torch_dtype=torch.bfloat16,
        token=config.HF_TOKEN or None,
        cache_dir=str(config.MODELS_DIR),
    )

    # Offload T5 + CLIP to CPU RAM between ops; transformer stays in VRAM.
    pipe.enable_model_cpu_offload()
    # Split VAE decode into slices so high-res outputs don't OOM.
    pipe.enable_vae_slicing()

    _pipeline = pipe
    logger.info("Pipeline ready.")


def is_loaded() -> bool:
    return _pipeline is not None


def prepare_image(img: Image.Image, max_side: int = 1024) -> Image.Image:
    """
    Resize so the longest edge ≤ max_side, then round both dimensions down
    to the nearest multiple of 16 (required by the FLUX VAE).

    A 4K phone photo at full res will OOM the VAE encoder; this keeps
    peak VRAM under control while preserving aspect ratio.
    """
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        w, h = int(w * scale), int(h * scale)
    # Round down to multiple of 16
    w = (w // 16) * 16
    h = (h // 16) * 16
    if (w, h) == img.size:
        return img
    return img.resize((w, h), Image.LANCZOS)


def edit_image(image: Image.Image, instruction: str, seed: int) -> Image.Image:
    """
    Apply instruction to image and return the edited PIL image.

    The same seed always produces the same output — this is what makes
    A/B comparisons honest: only the instruction changes, not the noise.
    """
    if _pipeline is None:
        raise RuntimeError("Pipeline not loaded. Call load_pipeline() first.")

    import torch
    # CPU generator is consistent regardless of which device runs the model.
    generator = torch.Generator("cpu").manual_seed(seed)

    result = _pipeline(
        image=image,
        prompt=instruction,
        guidance_scale=config.GUIDANCE_SCALE,
        num_inference_steps=config.NUM_INFERENCE_STEPS,
        generator=generator,
    )

    return result.images[0]


# ── CLI ───────────────────────────────────────────────────────────────────────
# Usage:  python -m app.pipeline --image samples/kitchen.jpg \
#                                --instruction "change the cabinets to matte navy" \
#                                --seed 42 --out out.png
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="FLUX.1 Kontext [dev] — single-image edit CLI"
    )
    parser.add_argument("--image", required=True, help="Path to input kitchen photo")
    parser.add_argument("--instruction", required=True, help="Edit instruction")
    parser.add_argument("--seed", type=int, default=config.DEFAULT_SEED)
    parser.add_argument("--out", default="out.png", help="Output path")
    parser.add_argument(
        "--steps",
        type=int,
        default=config.NUM_INFERENCE_STEPS,
        help="Number of denoising steps",
    )
    parser.add_argument(
        "--guidance",
        type=float,
        default=config.GUIDANCE_SCALE,
        help="Guidance scale",
    )
    args = parser.parse_args()

    # Allow CLI overrides of the defaults from config
    config.NUM_INFERENCE_STEPS = args.steps
    config.GUIDANCE_SCALE = args.guidance

    load_pipeline()

    img = Image.open(args.image).convert("RGB")
    logger.info(
        "Running: seed=%d steps=%d guidance=%.1f",
        args.seed, args.steps, args.guidance,
    )
    out = edit_image(img, args.instruction, args.seed)
    out.save(args.out)
    logger.info("Saved → %s", args.out)

    # Reproducibility check: run again with same seed, compare pixel hashes.
    import hashlib, io
    def _img_hash(im: Image.Image) -> str:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return hashlib.sha256(buf.getvalue()).hexdigest()[:12]

    out2 = edit_image(img, args.instruction, args.seed)
    h1, h2 = _img_hash(out), _img_hash(out2)
    if h1 == h2:
        logger.info("Seed reproducibility check PASSED (%s)", h1)
    else:
        logger.warning(
            "Seed reproducibility check FAILED: run1=%s run2=%s", h1, h2
        )
