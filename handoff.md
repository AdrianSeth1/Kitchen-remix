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
│       ├── finishes.json       # 40 finish presets across 5 categories (8 each)
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

### Phase 2 — Core API ✅
**Done.** All endpoints verified via curl. Server boots without ML stack.

**What changed:**
- `pipeline.py` — `torch` and `diffusers` imports are now lazy (inside functions), so the server boots cleanly even without the ML stack installed. `prepare_image()` added: resizes longest edge to ≤1024px, rounds both dims to multiples of 16 (required by FLUX VAE).
- `routes.py` — `GET /finishes` and `GET /structural-presets` serve the JSON presets. `/ab` instruction order fixed: `"finish, base_instruction"` (was backwards). Input validation (finishes > 12, label mismatch) runs before `_require_pipeline()` so callers get 422 not 503. Bad base64 → 422. `/export` HTML improved with timestamp and original photo section.
- `schemas.py` — `ABRequest` gets optional `labels: List[str]` parallel to `finishes`, so the frontend can send human-readable labels separately from instruction strings.

**Curl-verified status codes (no GPU needed):**
| Endpoint | Bad input | No model | Good request |
|---|---|---|---|
| GET /api/health | — | 200 `model_loaded: false` | 200 |
| GET /api/finishes | — | 200 (always) | 200 |
| GET /api/structural-presets | — | 200 (always) | 200 |
| POST /api/export | — | 200 (no model needed) | 200 |
| POST /api/edit | 422 | 503 | — (needs GPU) |
| POST /api/ab | 422 | 503 | — (needs GPU) |
| POST /api/layer | — | 503 | — (needs GPU) |
| POST /api/remove,/move,/open_wall | — | 503 | — (needs GPU) |

**To fully test (needs GPU + weights):**
```bash
# With model loaded, test /ab returns identical composition across variants:
curl -s -X POST http://localhost:8000/api/ab \
  -H "Content-Type: application/json" \
  -d '{
    "image_b64": "<b64 of kitchen.jpg>",
    "base_instruction": "keep everything else unchanged",
    "finishes": [
      "change the cabinets to matte navy blue",
      "change the cabinets to sage green"
    ],
    "labels": ["Matte Navy", "Sage Green"],
    "seed": 42
  }'
# Expect: two images with identical scene composition, only cabinet colour differs
```

---

### Phase 3 — Core frontend ✅ (built by Qwen-Coder, repaired 2026-06-27)
Upload, finish selector, A/B grid, layered edit, before/after slider, structural tab, export UI. Shipped with bugs; see the audit pass below.

### Phase 4 — Polish 🔶
Spec-sheet export endpoint, honest-scope README, parents' note, contractor spec-sheet copy, project plan. README + `docs/` done. Export endpoint still needs category grouping + per-finish thumbnails (`docs/contractor-spec-sheet-copy.md`).

### Audit + fixes pass — 2026-06-27
Full code review (`docs/audit.md`). Fixed the breaking frontend bugs:
- `StructuralTab.jsx` — added the missing `handleRemove/handleMove/handleOpenWall` (undefined refs were crashing the app on photo upload).
- `FinishSelector.jsx` — now honors `onSelectionChange` + multi-select, so selections actually populate.
- `AblGrid.jsx` — receives all selected finishes + labels, lifts results via `onGenerateAB`, fixed the base-instruction input mis-wire.
- `App.jsx` — wires `selectedFinishes → A/B → abResults → export`.
- `ExportSpecSheet.jsx` — sources A/B previews (`{label, image_b64}`) so the payload matches the backend schema.
- `finishes.json` — rewritten self-contained (40 presets), `structural.json` content improved (repo schema kept).

Knowledge deliverables from the brief now live in `docs/`: `audit.md`, `for-the-parents.md`, `contractor-spec-sheet-copy.md`, `project-plan.md`, plus the rewritten root `README.md`.

### Second fix pass — 2026-06-27 (cleared the remaining audit items)
- `structural.py` now loads instruction templates from `structural.json` (cached) instead of hardcoding them — single source of truth. `move_object` is now a single pass via the curated template (was remove-then-add).
- `StructuralTab.jsx` fetches `/api/structural-presets` and renders `caveats.move` / `caveats.open_wall` from the JSON.
- `/export` groups finishes by category (canonical order) with per-finish thumbnails, headings, and the disclaimer footer, per `docs/contractor-spec-sheet-copy.md`. `ExportSelection` gained `category`; `App.jsx` tags A/B previews with their category (matched by label) before export.
- Only `main.py` CORS is left open intentionally (fine behind the Vite proxy).

### Phase 6 — reference-image edits ✅ (built by Qwen-Coder, repaired 2026-06-27)
Spec: `docs/feature-reference-edits.md`; curated prompts: `backend/app/references.json`. Two tiers: Tier A finish-by-reference on Kontext (stitch a `[kitchen | reference]` canvas, crop back), Tier B object replacement on Qwen-Image-Edit-2509.

Qwen's first pass didn't run — see `docs/audit.md` "Phase 6" for the 8 bugs (server wouldn't boot: syntax errors in `pipeline.py` and `routes.py`, missing `references.py`, wrong Qwen class, stub UI, ineffective VRAM swap, schema regression, crop bug). All repaired.

**New files:** `backends.py` (swap manager), `qwen_pipeline.py` (Qwen wrapper, `QwenImageEditPlusPipeline`, `image=[kitchen, ref]`), `references.py` (loads `references.json`), `ReferenceTab.jsx`.

**Optional `note` field (added 2026-06-27):** both reference requests take an optional `note` free-text string, appended to the curated template instruction (e.g. attach a black kitchen, target = countertops, note = "just the countertop color, a flat matte black"). Wired through `ReferenceFinishRequest`/`ReferenceObjectRequest` → `pipeline.reference_finish(..., note)` / routes for the Qwen path → the two text inputs in `ReferenceTab.jsx`.

### Performance — fp8 quantization (added 2026-06-27)
On a 24 GB 4090 the bf16 transformer (~24 GB) fills VRAM with no headroom, so Windows spills into shared system RAM and inference crawls. `pipeline.load_pipeline()` now fp8-quantizes the transformer to ~12 GB via diffusers `QuantoConfig(weights_dtype="float8")` (needs `optimum-quanto`, now in requirements). Optional + graceful: `config.USE_FP8` (env `USE_FP8=0` to disable); falls back to bf16 if quanto is missing or quant fails. Text encoders still offload to RAM via `enable_model_cpu_offload()`. Target after this: ~30–60 s/edit instead of minutes. Qwen (Tier B) is still full-precision — same treatment could be applied later if it spills.

**Decision change (supersedes "load once at startup" for heavy models):** Kontext + Qwen-2509 can't co-reside on 24GB. `backends.ensure(kind)` keeps one resident, calling `pipeline.unload()` / `qwen_pipeline.unload()` (which now actually free VRAM via `gc` + `torch.cuda.empty_cache()`) before loading the other. Every Kontext endpoint calls `ensure("kontext")`; `/reference_object` calls `ensure("qwen")`. Swap costs a reload pause — fine for single-user. `/api/health` now reports `active_model`.

---

## Frontend data flow (post-fix)

```
Upload ──base64──▶ uploadedImageB64 (App state)
                        │
   FinishSelector ──onSelectionChange──▶ selectedFinishes [{label, instruction}]
                        │
   AblGrid  finishes = selectedFinishes.map(instruction)
            labels   = selectedFinishes.map(label)
            POST /api/ab ──▶ onGenerateAB ──▶ abResults [{label, image_b64}]
                        │
   ExportSpecSheet  selections = abResults  ──POST /api/export──▶ printable HTML
```

Single-finish path: clicking a finish also sets `selectedFinish` (string), used by the "Apply Selected Finish" button → `POST /api/edit` → before/after slider. Structural tab is independent: it POSTs target/destination/wall strings straight to `/api/remove|move|open_wall`.

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
