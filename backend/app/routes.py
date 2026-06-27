"""
All API endpoints. Registered in main.py via app.include_router(router).
Heavy inference calls run in a threadpool to avoid blocking the event loop.
"""
from __future__ import annotations

import base64
import io
import logging
from functools import partial

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from PIL import Image

from . import pipeline, structural
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


# ── helpers ──────────────────────────────────────────────────────────────────

def _b64_to_pil(b64: str) -> Image.Image:
    data = base64.b64decode(b64)
    return Image.open(io.BytesIO(data)).convert("RGB")


def _pil_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _require_pipeline() -> None:
    if not pipeline.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded yet")


# ── core ─────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok", "model_loaded": pipeline.is_loaded()}


@router.post("/edit", response_model=EditResponse)
async def edit(req: EditRequest):
    _require_pipeline()
    img = _b64_to_pil(req.image_b64)
    result = await run_in_threadpool(
        pipeline.edit_image, img, req.instruction, req.seed
    )
    return EditResponse(image_b64=_pil_to_b64(result))


@router.post("/ab", response_model=ABResponse)
async def ab(req: ABRequest):
    _require_pipeline()
    img = _b64_to_pil(req.image_b64)
    results: list[ABResult] = []
    for finish in req.finishes:
        instruction = f"{req.base_instruction} {finish}"
        out = await run_in_threadpool(pipeline.edit_image, img, instruction, req.seed)
        results.append(ABResult(label=finish, image_b64=_pil_to_b64(out)))
    return ABResponse(results=results)


@router.post("/layer", response_model=LayerResponse)
async def layer(req: LayerRequest):
    _require_pipeline()
    current = _b64_to_pil(req.image_b64)
    steps: list[LayerStep] = []
    for instruction in req.steps:
        current = await run_in_threadpool(
            pipeline.edit_image, current, instruction, req.seed
        )
        steps.append(LayerStep(instruction=instruction, image_b64=_pil_to_b64(current)))
    return LayerResponse(final_b64=_pil_to_b64(current), steps=steps)


@router.post("/export", response_model=ExportResponse)
async def export_spec(req: ExportRequest):
    rows = "".join(
        f"""
        <div class="tile">
          <img src="data:image/png;base64,{s.image_b64}" />
          <p>{s.label}</p>
        </div>"""
        for s in req.selections
    )
    final_section = ""
    if req.final_b64:
        final_section = (
            f'<h2>Final composite</h2>'
            f'<img src="data:image/png;base64,{req.final_b64}" class="final" />'
        )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Kitchen Remix — Spec Sheet</title>
<style>
  body {{ font-family: sans-serif; padding: 2rem; }}
  .grid {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
  .tile {{ width: 200px; text-align: center; }}
  .tile img {{ width: 100%; border-radius: 4px; }}
  .final {{ max-width: 600px; display: block; margin: 1rem 0; }}
  h1 {{ margin-bottom: 1rem; }}
</style>
</head>
<body>
<h1>Kitchen Remix — Finish Spec Sheet</h1>
<div class="grid">{rows}</div>
{final_section}
</body>
</html>"""
    return ExportResponse(html=html)


# ── structural (experimental) ─────────────────────────────────────────────────

@router.post("/remove", response_model=RemoveResponse)
async def remove(req: RemoveRequest):
    _require_pipeline()
    img = _b64_to_pil(req.image_b64)
    result = await run_in_threadpool(
        structural.remove_object, img, req.target, req.seed
    )
    return RemoveResponse(image_b64=_pil_to_b64(result))


@router.post("/move", response_model=MoveResponse)
async def move(req: MoveRequest):
    _require_pipeline()
    img = _b64_to_pil(req.image_b64)
    result = await run_in_threadpool(
        structural.move_object, img, req.target, req.destination, req.seed
    )
    return MoveResponse(image_b64=_pil_to_b64(result), approximate=True)


@router.post("/open_wall", response_model=OpenWallResponse)
async def open_wall(req: OpenWallRequest):
    _require_pipeline()
    img = _b64_to_pil(req.image_b64)
    result = await run_in_threadpool(
        structural.open_wall, img, req.wall_description, req.seed
    )
    return OpenWallResponse(image_b64=_pil_to_b64(result), invented_space=True)
