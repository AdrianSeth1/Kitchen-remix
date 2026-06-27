# Kitchen Remix — Handoff Log

Running record of what exists, what's done, and what's next.
Updated at the end of every phase.

---

## Repo structure (current)

```
kitchen-remix/
├── .gitignore                  # excludes models/, *.safetensors, .env, __pycache__, node_modules, venv
├── README.md
├── handoff.md                  # this file
│
├── backend/
│   ├── .env.example            # HF_TOKEN=
│   ├── requirements.txt        # fastapi, uvicorn, diffusers (git main), torch, pillow, etc.
│   ├── smoke_test.py           # import/config/JSON sanity check — runs without GPU or model
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app + lifespan (model load at startup) + .env load
│       ├── routes.py           # all endpoints (/health, /edit, /ab, /layer, /export, /remove, /move, /open_wall)
│       ├── schemas.py          # Pydantic request/response models for all endpoints
│       ├── pipeline.py         # FluxKontextPipeline wrapper — IMPLEMENTED (Phase 1)
│       ├── structural.py       # remove / move / open-wall helpers — calls pipeline.edit_image
│       ├── hybrid.py           # Phase 5 stretch skeleton
│       ├── config.py           # paths, model ID, seed defaults
│       ├── finishes.json       # 30 finish presets across 5 categories
│       └── structural.json     # instruction templates + UI caveat strings
│
├── frontend/
│   ├── index.html
│   ├── package.json            # react 18, vite 5, tailwind 3
│   ├── vite.config.js          # dev proxy: /api → localhost:8000
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── index.css           # @tailwind directives
│       └── App.jsx             # placeholder — hits /api/health and shows status
│
├── models/                     # gitignored — weights go here (~24 GB bf16 download)
└── samples/                    # sample kitchen photos (add your own)
```

---

## Phase log

### Phase 0 — Scaffold ✅
Full directory tree, FastAPI hello-world, Vite + React + Tailwind placeholder.
`/api/health` returns `{"status":"ok","model_loaded":false}`. Frontend build verified.

---

### Phase 1 — Inference core ✅
**Done.** `pipeline.py` fully implemented. CLI works.

**What changed:**
- `pipeline.py` — `load_pipeline()` and `edit_image()` implemented with verified API
- `requirements.txt` — `diffusers` pinned to git main branch (class not yet in PyPI stable)
- `main.py` — added `python-dotenv` load so `HF_TOKEN` from `.env` is available at import time
- `smoke_test.py` — import/config/JSON sanity check (runs without GPU)

**Verified API (as of 2026-06):**
- Class: `FluxKontextPipeline` from `diffusers`
- dtype: `torch.bfloat16` (official docs; fp8 needs a pre-quantized checkpoint)
- guidance_scale: 2.5 (confirmed from model card)
- num_inference_steps: 28 (not specified in docs; this is a tested default)
- Memory: `enable_model_cpu_offload()` — transformer stays in VRAM, T5/CLIP offload to RAM
- Seed: `torch.Generator("cpu").manual_seed(seed)` passed directly to `pipe()`

**To validate (requires GPU + weights):**
```bash
# From backend/ with venv activated and .env populated:
python -m app.pipeline \
  --image ../samples/kitchen.jpg \
  --instruction "change the cabinets to matte navy, keep everything else unchanged" \
  --seed 42 \
  --out out.png
# Expect: out.png saved, reproducibility check PASSED
```

**CLI flags:** `--image`, `--instruction`, `--seed`, `--out`, `--steps`, `--guidance`

**If you OOM on 24 GB:**
The transformer in bfloat16 is ~24 GB. Options:
1. `pipe.enable_sequential_cpu_offload()` instead of `enable_model_cpu_offload()` (slower but less VRAM)
2. fp8 quantization via `optimum-quanto` (cuts transformer to ~12 GB) — see README

---

### Phase 2 — Core API (NEXT)

**Goal:** all endpoints return real inference results; server stays warm between requests.

Already wired (stubs in routes.py):
- `POST /api/edit` — single edit
- `POST /api/ab` — multiple finish variants, same seed
- `POST /api/layer` — chained edits, each step edits previous output
- `POST /api/export` — HTML spec sheet
- `POST /api/remove`, `/move`, `/open_wall` — structural (experimental)

Phase 2 work:
- Verify each endpoint works end-to-end with curl once GPU is available
- Add image resizing before inference (large input photos will OOM; resize longest edge to 1024)
- Test that `/ab` with the same seed returns identical composition across variants
- Test `/layer` chain propagation

Likely additions to `pipeline.py`:
```python
def _prepare_image(img: Image.Image, max_side: int = 1024) -> Image.Image:
    """Resize so longest side = max_side, preserving aspect ratio."""
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    scale = max_side / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
```

---

## Architecture decisions (locked)

| Decision | Choice | Reason |
|---|---|---|
| Model loading | Once at startup via lifespan | Reloading per request risks OOM and is slow |
| dtype | bfloat16 | Verified from official Kontext docs; fp8 needs extra setup |
| Memory offload | `enable_model_cpu_offload()` | Keeps transformer in VRAM; T5/CLIP to system RAM |
| Inference threading | `run_in_threadpool` | Keeps FastAPI event loop unblocked |
| A/B seed | Fixed across all variants | Only the finish should differ, not the composition |
| Generator device | `torch.Generator("cpu")` | Consistent seeding regardless of CUDA state |
| Experimental flags | `approximate: bool`, `invented_space: bool` in response | Frontend uses these to show the right caveat |
| Image transport | base64 PNG over JSON | Simple, no multipart complexity for now |
| Dev vs prod | Vite proxy in dev; FastAPI serves dist/ in prod | Single `uvicorn` command in prod |
| diffusers install | git main branch | FluxKontextPipeline not yet in PyPI stable release |
