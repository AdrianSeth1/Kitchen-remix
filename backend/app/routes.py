"""
All API endpoints. Registered in main.py via app.include_router(router).
Heavy inference calls run in a threadpool to avoid blocking the event loop.
"""
from __future__ import annotations

import base64
import binascii
import html
import io
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from . import config, pipeline, qwen_pipeline, structural, backends, references
from .schemas import (
    ABRequest, ABResponse, ABResult,
    EditRequest, EditResponse,
    ExportRequest, ExportResponse,
    LayerRequest, LayerResponse, LayerStep,
    MoveRequest, MoveResponse,
    OpenWallRequest, OpenWallResponse,
    RemoveRequest, RemoveResponse,
    ReferenceFinishRequest, ReferenceFinishResponse,
    ReferenceObjectRequest, ReferenceObjectResponse,
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


def _active_model() -> str:
    if pipeline.is_loaded():
        return "kontext"
    if qwen_pipeline.is_loaded():
        return "qwen"
    return "none"


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


@router.get("/reference-presets")
def get_reference_presets():
    """Return references.json — prompt templates and caveats for reference edits."""
    return JSONResponse(json.loads(config.REFERENCES_JSON.read_text(encoding="utf-8")))


# ── core ─────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": pipeline.is_loaded(),
        "active_model": _active_model(),
    }


@router.post("/edit", response_model=EditResponse)
async def edit(req: EditRequest):
    backends.ensure("kontext")
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
    backends.ensure("kontext")
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
    backends.ensure("kontext")
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

    # Group finishes by category, in the canonical kitchen order; anything
    # without a known category falls to the end.
    order = ["cabinets", "countertops", "backsplash", "flooring", "paint"]
    groups: dict[str, list] = {}
    for s in req.selections:
        groups.setdefault((s.category or "other").lower(), []).append(s)
    ordered = [(c, groups[c]) for c in order if c in groups]
    ordered += [(c, v) for c, v in groups.items() if c not in order]

    def _tile(s) -> str:
        label = html.escape(s.label)
        cat = html.escape((s.category or "").capitalize())
        detail = f"{cat} — {label}" if cat else label
        return (
            f'<div class="tile">'
            f'<img src="data:image/png;base64,{s.image_b64}" alt="{label}" />'
            f'<p class="name">{label}</p>'
            f'<p class="detail">{detail}</p>'
            f"</div>"
        )

    if ordered:
        finishes_html = "".join(
            f'<h3>{html.escape(cat.capitalize())}</h3>'
            f'<div class="grid">{"".join(_tile(s) for s in items)}</div>'
            for cat, items in ordered
        )
    else:
        finishes_html = '<p class="detail">No finishes selected.</p>'

    final_section = ""
    if req.final_b64:
        final_section = (
            '<h2>Combined preview</h2>'
            f'<img src="data:image/png;base64,{req.final_b64}" class="final" alt="Combined preview" />'
            '<p class="detail">All selected finishes shown together (approximate).</p>'
        )

    html_doc = f"""<!DOCTYPE html>
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
  h2 {{ font-size: 1rem; margin: 1.75rem 0 0.75rem; text-transform: uppercase;
        letter-spacing: 0.05em; color: #444; }}
  h3 {{ font-size: 0.85rem; margin: 1rem 0 0.5rem; color: #222; }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
  .tile, .original {{ width: 200px; text-align: center; }}
  .tile img, .original img {{ width: 100%; border-radius: 6px;
                              border: 1px solid #e5e5e5; display: block; }}
  .name {{ font-size: 0.85rem; font-weight: 600; margin-top: 0.4rem; color: #1a1a1a; }}
  .detail {{ font-size: 0.75rem; margin-top: 0.15rem; color: #666; }}
  .final {{ max-width: 640px; display: block; border-radius: 6px;
            border: 1px solid #e5e5e5; margin: 0.5rem 0 0.5rem; }}
  footer {{ margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #e5e5e5;
            font-size: 0.7rem; color: #888; line-height: 1.5; }}
  @media print {{
    body {{ padding: 1cm; }}
    h2 {{ page-break-before: auto; }}
  }}
</style>
</head>
<body>
<h1>Kitchen Remix — Finish Spec Sheet</h1>
<p class="meta">Prepared for contractor review · Generated {timestamp}</p>

<h2>Current kitchen</h2>
<div class="grid">
  <div class="original">
    <img src="data:image/png;base64,{req.original_b64}" alt="Current kitchen" />
    <p class="detail">Starting photo — finishes below are applied to this room.</p>
  </div>
</div>

<h2>Selected finishes</h2>
{finishes_html}

{final_section}

<footer>These are AI-generated previews of color and material only. They are not measured
drawings. Colors vary by screen, lighting, and product batch — confirm against physical
samples before ordering. Any layout or structural changes shown elsewhere are approximate
and not included here.</footer>
</body>
</html>"""
    return ExportResponse(html=html_doc)


# ── structural (experimental) ─────────────────────────────────────────────────

@router.post("/remove", response_model=RemoveResponse)
async def remove(req: RemoveRequest):
    backends.ensure("kontext")
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    result = await run_in_threadpool(
        structural.remove_object, img, req.target, req.seed
    )
    return RemoveResponse(image_b64=_pil_to_b64(result))


@router.post("/move", response_model=MoveResponse)
async def move(req: MoveRequest):
    backends.ensure("kontext")
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    result = await run_in_threadpool(
        structural.move_object, img, req.target, req.destination, req.seed
    )
    return MoveResponse(image_b64=_pil_to_b64(result), approximate=True)


@router.post("/open_wall", response_model=OpenWallResponse)
async def open_wall(req: OpenWallRequest):
    backends.ensure("kontext")
    _require_pipeline()
    img = pipeline.prepare_image(_b64_to_pil(req.image_b64))
    result = await run_in_threadpool(
        structural.open_wall, img, req.wall_description, req.seed
    )
    return OpenWallResponse(image_b64=_pil_to_b64(result), invented_space=True)


# ── reference edits ───────────────────────────────────────────────────────────

@router.post("/reference_finish", response_model=ReferenceFinishResponse)
async def reference_finish(req: ReferenceFinishRequest):
    """Tier A — apply a finish/style from an attached reference photo (Kontext)."""
    if req.target not in references.FINISH_REFERENCE_TEMPLATES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown target '{req.target}'. "
                   f"Valid targets: {list(references.FINISH_REFERENCE_TEMPLATES)}",
        )
    kitchen_img = _b64_to_pil(req.image_b64)
    reference_img = _b64_to_pil(req.reference_b64)

    backends.ensure("kontext")
    if not pipeline.is_loaded():
        raise HTTPException(status_code=503, detail="Kontext model not loaded yet")

    result = await run_in_threadpool(
        pipeline.reference_finish,
        kitchen_img, reference_img, req.target, req.seed, req.note,
    )
    return ReferenceFinishResponse(image_b64=_pil_to_b64(result), style_only=True)


@router.post("/reference_object", response_model=ReferenceObjectResponse)
async def reference_object(req: ReferenceObjectRequest):
    """Tier B — replace an appliance with one matching a reference (Qwen-2509)."""
    if req.target not in references.OBJECT_REFERENCE_TEMPLATES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown target '{req.target}'. "
                   f"Valid targets: {list(references.OBJECT_REFERENCE_TEMPLATES)}",
        )
    kitchen_img = _b64_to_pil(req.image_b64)
    reference_img = _b64_to_pil(req.reference_b64)
    instruction = references.OBJECT_REFERENCE_TEMPLATES[req.target]
    if req.note.strip():
        instruction = f"{instruction} {req.note.strip()}"

    backends.ensure("qwen")
    if not qwen_pipeline.is_loaded():
        raise HTTPException(status_code=503, detail="Qwen model not loaded yet")

    result = await run_in_threadpool(
        qwen_pipeline.edit_with_references,
        kitchen_img, [reference_img], instruction, req.seed,
    )
    return ReferenceObjectResponse(
        image_b64=_pil_to_b64(result), style_accurate=True, spec_accurate=False
    )
