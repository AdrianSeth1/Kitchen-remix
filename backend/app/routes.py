"""
All API endpoints. Registered in main.py via app.include_router(router).
Heavy inference calls run in a threadpool to avoid blocking the event loop.
"""
from __future__ import annotations

import base64
import binascii
import io
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from . import config, pipeline, structural
from .schemas import (
    ABRequest, ABResponse, ABResult,
    EditRequest, EditResponse,
    ExportRequest, ExportResponse,
    LayerRequest, LayerResponse, LayerStep,
    MoveRequest, MoveResponse,
    OpenWallRequest, OpenWallResponse,
    RemoveRequest, RemoveResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_AB_MAX_FINISHES = 12  # guard against absurdly long batches


# ── helpers ───────────────────────────────────────────────────────────────────

def _b64_to_pil(b64: str) -> Image.Image:
    """Decode base64 → PIL Image. Raises HTTP 422 on bad input."""
    try:
        data = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail="image_b64 is not valid base64")
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=422, detail="image_b64 is not a recognised image format")


def _pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _require_pipeline() -> None:
    if not pipeline.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded yet")


def _ab_instruction(finish: str, base: str) -> str:
    """
    Compose a finish instruction for A/B.

    finish is the full finish instruction  ("change the cabinets to matte navy blue").
    base is an optional common qualifier   ("keep everything else unchanged").
    Together: "change the cabinets to matte navy blue, keep everything else unchanged".
    """
    base = base.strip()
    finish = finish.strip()
    if base:
        return f"{finish}, {base}"
    return finish


# ── presets ───────────────────────────────────────────────────────────────────

@router.get("/finishes")
def get_finishes():
    """Return finishes.json — category → list of {label, instruction} presets."""
    return JSONResponse(json.loads(config.FINISHES_JSON.read_text(encoding="utf-8")))


@router.get("/structural-presets")
def get_structural_presets():
    """Return structural.json — instruction templates and UI caveat strings."""
    return JSONResponse(json.loads(config.STRUCTURAL_JSON.read_text(encoding="utf-8")))


# ── core ─────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok", "model_loaded": pipeline.is_loaded()}


@router.post("/edit", response_model=EditResponse)
async def edit(req: EditRequest):
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    result = await run_in_threadpool(
        pipeline.edit_image, img, req.instruction, req.seed
    )
    return EditResponse(image_b64=_pil_to_b64(result))


@router.post("/ab", response_model=ABResponse)
async def ab(req: ABRequest):
    # Validate inputs before checking model so callers get 422 not 503.
    if len(req.finishes) > _AB_MAX_FINISHES:
        raise HTTPException(
            status_code=422,
            detail=f"Too many finishes ({len(req.finishes)}); max is {_AB_MAX_FINISHES}",
        )
    if req.labels is not None and len(req.labels) != len(req.finishes):
        raise HTTPException(
            status_code=422,
            detail="labels length must match finishes length",
        )
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    results: list[ABResult] = []
    for i, finish in enumerate(req.finishes):
        label = req.labels[i] if req.labels else finish
        instruction = _ab_instruction(finish, req.base_instruction)
        logger.info("A/B variant %d/%d: %s", i + 1, len(req.finishes), instruction)
        out = await run_in_threadpool(pipeline.edit_image, img, instruction, req.seed)
        results.append(ABResult(label=label, image_b64=_pil_to_b64(out)))
    return ABResponse(results=results)


@router.post("/layer", response_model=LayerResponse)
async def layer(req: LayerRequest):
    _require_pipeline()
    current = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    steps: list[LayerStep] = []
    for i, instruction in enumerate(req.steps):
        logger.info("Layer step %d/%d: %s", i + 1, len(req.steps), instruction)
        current = await run_in_threadpool(
            pipeline.edit_image, current, instruction, req.seed
        )
        steps.append(LayerStep(instruction=instruction, image_b64=_pil_to_b64(current)))
    return LayerResponse(final_b64=_pil_to_b64(current), steps=steps)


@router.post("/export", response_model=ExportResponse)
async def export_spec(req: ExportRequest):
    """Generate a printable HTML spec sheet of selected finishes."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    tile_rows = "".join(
        f'<div class="tile">'
        f'<img src="data:image/png;base64,{s.image_b64}" alt="{s.label}" />'
        f"<p>{s.label}</p>"
        f"</div>"
        for s in req.selections
    )

    original_section = (
        f'<div class="original">'
        f'<img src="data:image/png;base64,{req.original_b64}" alt="Original" />'
        f"<p>Original</p>"
        f"</div>"
    )

    final_section = ""
    if req.final_b64:
        final_section = (
            '<h2>Final composite</h2>'
            f'<img src="data:image/png;base64,{req.final_b64}" class="final" alt="Final" />'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Kitchen Remix — Spec Sheet</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; padding: 2rem; color: #1a1a1a; background: #fff; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
  .meta {{ font-size: 0.8rem; color: #666; margin-bottom: 2rem; }}
  h2 {{ font-size: 1rem; margin: 1.5rem 0 0.75rem; text-transform: uppercase;
        letter-spacing: 0.05em; color: #444; }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
  .tile, .original {{ width: 200px; text-align: center; }}
  .tile img, .original img {{ width: 100%; border-radius: 6px;
                              border: 1px solid #e5e5e5; display: block; }}
  .tile p, .original p {{ font-size: 0.8rem; margin-top: 0.4rem; color: #333; }}
  .final {{ max-width: 640px; display: block; border-radius: 6px;
            border: 1px solid #e5e5e5; margin: 0.5rem 0 1.5rem; }}
  @media print {{
    body {{ padding: 1cm; }}
    h2 {{ page-break-before: auto; }}
  }}
</style>
</head>
<body>
<h1>Kitchen Remix — Finish Spec Sheet</h1>
<p class="meta">Generated {timestamp}</p>

<h2>Original</h2>
<div class="grid">{original_section}</div>

<h2>Selected finishes</h2>
<div class="grid">{tile_rows}</div>

{final_section}
</body>
</html>"""
    return ExportResponse(html=html)


# ── structural (experimental) ─────────────────────────────────────────────────

@router.post("/remove", response_model=RemoveResponse)
async def remove(req: RemoveRequest):
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    result = await run_in_threadpool(
        structural.remove_object, img, req.target, req.seed
    )
    return RemoveResponse(image_b64=_pil_to_b64(result))


@router.post("/move", response_model=MoveResponse)
async def move(req: MoveRequest):
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    result = await run_in_threadpool(
        structural.move_object, img, req.target, req.destination, req.seed
    )
    return MoveResponse(image_b64=_pil_to_b64(result), approximate=True)


@router.post("/open_wall", response_model=OpenWallResponse)
async def open_wall(req: OpenWallRequest):
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    result = await run_in_threadpool(
        structural.open_wall, img, req.wall_description, req.seed
    )
    return OpenWallResponse(image_b64=_pil_to_b64(result), invented_space=True)
