# Kitchen Remix

**Take a photo of a real kitchen and preview remodel options (new cabinets, countertops, backsplash, flooring, paint) as photorealistic edits, before spending a dollar on the real thing.**

It runs a local image-editing model (FLUX.1 Kontext) on a home RTX 4090, so the photos never leave the machine. It's also deliberately honest about what an image model can and can't know, and that honesty is the most interesting engineering decision here, so it's documented up front rather than buried.

---

## The problem

Most people remodeling a kitchen can't picture the result. Showroom samples and Pinterest boards don't show *your* kitchen with that finish, and a designer's renders cost money and time. This was built for the people who wanted to compare a few directions before committing, my parents, without learning CAD or paying for mockups.

The trap with AI image tools is that they'll cheerfully generate anything, including changes the model has no real basis for. A confident render of a wall that isn't there is worse than no render: it invites a real decision based on a guess. So the design question wasn't "what *can* the model do?" but "what can it do **reliably**, and how do we keep the rest clearly labeled?"

## The approach: honest scope tiers

Every edit is sorted into one of three tiers by how much the model has to invent.

| Tier | Edits | Why it's trustworthy (or not) |
| --- | --- | --- |
| **Core** (reliable) | Finish swaps (cabinets, countertops, backsplash, flooring, paint), A/B comparison, layered edits, object removal | None of these need information the photo doesn't already contain. A surface change, or filling in a wall the model can already see. Treated as dependable previews. |
| **Experimental** (approximate) | Moving an object; opening or removing a wall | The model invents geometry it can't actually know (the scale of a moved object, the room beyond a wall). Labeled in-app as *not dimensionally accurate*: directional feel, not measurement. |
| **Stretch** (accurate structural) | User supplies the new layout as a geometry control (depth map, edge image, or rough blockout); the model only adds realism on top | The honest way to do structural change: the layout comes from the user, the model just renders it. |

Showing where the line sits, and refusing to let the model cross it silently, is the whole point.

## How it works

```
Browser (React)        FastAPI backend         FLUX.1 Kontext
─────────────────      ────────────────        ──────────────
upload a photo  ──base64 PNG──▶  validate + resize  ──image──▶  loaded once at
pick finishes                    to a model-safe size           startup, kept
hit "compare"           ▲                                       warm in VRAM
                        └──────── edited images ── inference in a threadpool
                                                    (event loop never blocks)
```

A photo is sent to the backend as base64, resized to a size the model's encoder can handle, then edited with a plain-English instruction like *"change the cabinets to matte sage green, keep everything else unchanged,"* with no manual masking for the core finishes. The **same random seed is reused across an A/B set**, so only the instruction changes between variants and the rest of the scene stays put. That's what makes the comparison fair.

The model loads once at startup and stays resident in GPU memory (reloading per request is slow and risks running out of memory), and inference runs in a worker thread so the API stays responsive. Two small JSON files, `finishes.json` and `structural.json`, hold the curated edit instructions as data, not code, so the preset library can grow without touching the pipeline.

## Architecture at a glance

| Layer | Choice | Why |
| --- | --- | --- |
| Editing model | FLUX.1 Kontext [dev], run locally | Instruction-based editing, no masking (Qwen-Image-Edit is the commercial-friendly fallback) |
| Backend | FastAPI + Pydantic | Typed request/response schemas; async endpoints |
| Inference | Loaded once at startup, run in a threadpool | Avoids reload cost and OOM; keeps the event loop free |
| Reproducibility | Fixed seed across an A/B set | Only the finish differs between variants, not the composition |
| Frontend | React + Vite + Tailwind | Fast dev loop; single-page UI |
| Hardware target | RTX 4090, 24 GB, bfloat16 | Fits the transformer in VRAM with CPU offload for the text encoders |

## What's built

Core finishes, A/B comparison, layered edits, object removal, the experimental structural modes (move / open wall) with caveats, and a one-page spec-sheet export for handing to a contractor. The hybrid geometry-controlled mode is scoped and stubbed, not yet wired in.

## Running it

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env                                # add your Hugging Face token
uvicorn app.main:app --reload
```
The server boots even without the ML stack installed. It just reports `model_loaded: false` until the weights are present, which keeps the API testable without a GPU.

**Frontend**
```bash
cd frontend
npm install
npm run dev        # dev server proxies /api to localhost:8000
```
In production, `npm run build` emits a static bundle that FastAPI serves directly, so the whole thing runs from one `uvicorn` command.

## A note on the model

FLUX.1 Kontext [dev] is used for local development and previews. For any commercial use, Qwen-Image-Edit is the intended fallback, and the pipeline wrapper is the only piece that would change.

---

Built as a practical tool for one family's remodel, and as a study in scoping an AI feature to what it can actually be trusted to do. By [Aryamaan Seth](https://www.linkedin.com/in/aryamaanseth/).
