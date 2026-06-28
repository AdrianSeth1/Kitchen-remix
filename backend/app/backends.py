"""
Coordinator so only one heavy model is resident at a time.

Kontext and Qwen-Image-Edit-2509 are each ~20GB+ in bf16 and cannot both fit on
a 24GB card. ensure(kind) unloads the other model (freeing its VRAM) before
loading the requested one. Single-user app, so a simple swap — and the reload
latency on switch — is acceptable.
"""
from . import pipeline, qwen_pipeline


def ensure(kind: str) -> None:
    """Make `kind` ("kontext" | "qwen") the resident model, unloading the other."""
    if kind == "kontext":
        if qwen_pipeline.is_loaded():
            qwen_pipeline.unload()
        if not pipeline.is_loaded():
            pipeline.load_pipeline()
    elif kind == "qwen":
        if pipeline.is_loaded():
            pipeline.unload()
        if not qwen_pipeline.is_loaded():
            qwen_pipeline.load_pipeline()
    else:
        raise ValueError(f"Unknown model kind: {kind}")
