# Kitchen Remix

Photorealistic kitchen remodel visualization powered by **FLUX.1 Kontext [dev]** running locally on an RTX 4090.

Upload a photo of your kitchen and explore finish swaps, layered edits, and structural experiments — all rendered with a diffusion model, side-by-side.

---

## What this does (and what it honestly cannot do)

| Feature | Reliability | Why |
|---|---|---|
| Finish swaps (cabinets, countertops, backsplash, flooring, paint) | **Reliable** | No new spatial information needed — the model only changes surface appearance |
| Object removal | **Reliable** | Filling a masked region with matching background is well-supported |
| Object relocation | **Approximate** | The model must invent placement — scale and depth may be wrong |
| Wall removal / opening | **Approximate** | The space beyond the wall is fabricated, not the real adjacent room |
| Geometry-controlled structural change (Phase 5) | **Accurate** | Only possible when the user supplies a geometry control (depth map, rendered blockout) |

The UI labels every experimental result visibly. Scale and placement in experimental results are directional only — good for feel, not for measurements.

---

## Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn, PyTorch + CUDA, diffusers, Pillow
- **Model:** FLUX.1 Kontext [dev] (fp8, loaded once at startup, kept warm in VRAM)
- **Frontend:** React 18, Vite, Tailwind CSS

---

## Setup

### 1. Clone and set up secrets

```bash
git clone <repo>
cd kitchen-remix
cp backend/.env.example backend/.env
# edit backend/.env and add your HF_TOKEN
```

### 2. Python environment

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
# Install PyTorch separately with your CUDA version:
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Run (dev)

Two terminals:

```bash
# Terminal 1 — backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
# opens http://localhost:5173
```

### 5. Run (production — single command)

```bash
cd frontend && npm run build
cd ../backend
uvicorn app.main:app --port 8000
# visit http://localhost:8000
```

---

## Architecture

```
kitchen-remix/
  backend/app/
    main.py        # FastAPI app, model loaded at startup via lifespan
    pipeline.py    # FLUX.1 Kontext wrapper — edit_image(image, instruction, seed)
    structural.py  # remove / move / open-wall helpers (Phase 3.5)
    hybrid.py      # Phase 5 stretch: geometry-controlled rendering
    routes.py      # all endpoints — inference runs in threadpool
    schemas.py     # Pydantic request / response models
    config.py      # paths, model IDs, defaults
    finishes.json  # finish presets by category
    structural.json# instruction templates and caveats
  frontend/src/
    App.jsx        # main app shell
    components/    # upload, A/B grid, layer editor, slider, structural tab
  models/          # weight cache — gitignored
  samples/         # sample kitchen photos
```

**Key design decisions:**

- Model loads once at startup and stays in VRAM — reloading per request risks OOM and is slow.
- Fixed seed is used across all A/B variants so only the finish changes, not the composition.
- Inference runs in a `run_in_threadpool` call so the FastAPI event loop is never blocked.
- `approximate: true` / `invented_space: true` flags travel with every experimental result so the UI always knows what to label.

---

## Development phases

- [x] **Phase 0** — Scaffold, `.gitignore`, FastAPI `/health`, Vite placeholder
- [ ] **Phase 1** — Inference core: `edit_image()` CLI, fp8 Kontext, seed reproducibility
- [ ] **Phase 2** — Core API: `/edit`, `/ab`, `/layer`, `/export`
- [ ] **Phase 3** — Core frontend: upload, A/B grid, layer editor, before/after slider
- [ ] **Phase 3.5** — Structural tab: remove, move, open-wall with caveat banners
- [ ] **Phase 4** — Polish: export spec sheet, sample photos, README demo
- [ ] **Phase 5** — Stretch: geometry-controlled rendering via ControlNet
