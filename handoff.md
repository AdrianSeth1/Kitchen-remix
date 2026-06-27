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
│   ├── requirements.txt        # fastapi, uvicorn, diffusers, torch, pillow, etc.
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app + lifespan (model load at startup)
│       ├── routes.py           # all endpoints (/health, /edit, /ab, /layer, /export, /remove, /move, /open_wall)
│       ├── schemas.py          # Pydantic request/response models for all endpoints
│       ├── pipeline.py         # FLUX.1 Kontext wrapper — STUB (Phase 1 fills this)
│       ├── structural.py       # remove / move / open-wall helpers — calls pipeline.edit_image
│       ├── hybrid.py           # Phase 5 stretch skeleton
│       ├── config.py           # paths, model ID, seed defaults
│       ├── finishes.json       # finish presets (cabinets, countertops, backsplash, flooring, paint)
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
├── models/                     # gitignored — weights go here
└── samples/                    # sample kitchen photos (empty for now)
```

---

## Phase log

### Phase 0 — Scaffold ✅
**Done.** Full directory tree, all stub files written.

What exists:
- `.gitignore` — excludes models/, *.safetensors, *.ckpt, *.bin, *.pt, .env, __pycache__, venv, node_modules, dist
- Backend: FastAPI app with lifespan hook, all routes wired (endpoints respond but inference is stubbed), Pydantic schemas, config, finishes.json, structural.json
- Frontend: Vite + React + Tailwind placeholder — polls `/api/health` on load and shows backend status
- `requirements.txt` — all deps listed; PyTorch install line is commented with a note to pin your CUDA version
- `README.md` — problem, architecture, honest scope table, run instructions

**Not yet done (stubs):**
- `pipeline.load_pipeline()` — logs a warning, does not load the model
- `pipeline.edit_image()` — raises NotImplementedError
- All inference endpoints return 503 until the model is loaded

### To start dev servers (Phase 0 check):

```bash
# Backend (from kitchen-remix/backend/)
python -m venv .venv && .venv\Scripts\activate
pip install fastapi uvicorn python-dotenv pillow pydantic
uvicorn app.main:app --reload --port 8000
# GET http://localhost:8000/api/health → {"status":"ok","model_loaded":false}

# Frontend (from kitchen-remix/frontend/)
npm install
npm run dev
# http://localhost:5173 — shows placeholder with backend status
```

---

## Phase 1 — Inference core (NEXT)

**Goal:** fill in `pipeline.py` so `edit_image()` actually runs FLUX.1 Kontext.

Steps:
1. Verify the current diffusers pipeline class for Kontext:
   - Check https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev model card
   - Run `python -c "import diffusers; print(diffusers.__version__)"` and check what's available
   - The class may be `FluxKontextPipeline` or similar — do not assume, verify
2. Implement `load_pipeline()` with fp8 quantization and `cache_dir=config.MODELS_DIR`
3. Implement `edit_image()` with a `torch.Generator` seeded deterministically
4. Add CLI: `python -m app.pipeline --image samples/kitchen.jpg --instruction "..." --seed 42 --out out.png`
5. Validate: same seed → same output; believable finish swap on a real photo

**Key decisions to make in Phase 1:**
- fp8 dtype: `torch.float8_e4m3fn` or `torch.bfloat16` fallback if fp8 is slow
- Whether to use `enable_model_cpu_offload()` or keep fully in VRAM (24GB should be enough for fp8)
- Confirm `guidance_scale` and `num_inference_steps` defaults for Kontext dev (check model card)

---

## Architecture decisions (locked)

| Decision | Choice | Reason |
|---|---|---|
| Model loading | Once at startup via lifespan | Reloading per request risks OOM and is slow |
| Inference threading | `run_in_threadpool` | Keeps FastAPI event loop unblocked |
| A/B seed | Fixed across all variants | Only the finish should differ, not the composition |
| Experimental flags | `approximate: bool`, `invented_space: bool` in response | Frontend uses these to show the right caveat |
| Image transport | base64 PNG over JSON | Simple, no multipart complexity for now |
| Dev vs prod | Vite proxy in dev; FastAPI serves dist/ in prod | Single `uvicorn` command in prod |
