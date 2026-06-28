# Kitchen Remix

Take a photo of a real kitchen and preview remodel options — new cabinets, countertops, backsplash, flooring, paint — as photorealistic edits, before spending a dollar on the real thing. It runs a local image-editing model (FLUX.1 Kontext) on a home RTX 4090, so the photos never leave the machine.

The project has a second purpose: it is built to be honest about what an image model can and cannot know. That honesty is the most interesting engineering decision here, so it is documented up front rather than buried.

## The problem

Most people remodeling a kitchen can't picture the result. Showroom samples and Pinterest boards don't show *your* kitchen with *that* finish, and a designer's renders cost money and time. The people this was built for — my parents — wanted to compare a few directions before committing, without learning CAD or paying for mockups.

The trap with AI image tools is that they will cheerfully generate *anything*, including changes the model has no real basis for. A confident render of a wall that isn't there is worse than no render: it invites a real decision based on a guess. So the design question wasn't "what can the model do?" but "what can the model do *reliably*, and how do we keep the rest clearly labeled?"

## The approach: honest scope tiers

Edits are sorted into three tiers by how much the model has to invent.

**Core — reliable.** Finish swaps (cabinets, countertops, backsplash, flooring, paint), A/B comparison, layered edits, and object removal. These are trustworthy because none of them require information the photo doesn't already contain. Repainting a cabinet or swapping a countertop is a surface change; removing an object only asks the model to rebuild walls and floor it can already see. The app treats these as dependable previews.

**Experimental — approximate.** Moving an object to a new spot, and opening or removing a wall. The model invents geometry it cannot actually know — the scale of the moved object, the room beyond the wall. These are directional only and labeled in the app as *not dimensionally accurate*. They convey feel, not measurement.

**Stretch — accurate structural.** A hybrid pipeline where the user supplies the new layout as a geometry control (a depth map, edge image, or rough blockout) and the model is restricted to adding realism on top of geometry it was *given*. This is the honest way to do structural change: the layout comes from the user, the model only renders it.

Showing where the line sits — and refusing to let the model cross it silently — is the point. It reads as engineering maturity precisely because overclaiming would have been easier.

## How it works (plain language)

```
  Browser (React)                 FastAPI backend                FLUX.1 Kontext
  ─────────────────               ───────────────                ──────────────
  upload a photo  ──base64 PNG──▶  validate + resize  ──image──▶  load once at
  pick finishes                    to a model-safe size           startup, stay
  hit "compare"                    │                              warm in VRAM
        ▲                          ▼
        └────────── edited images ── run inference in a
                                      threadpool (event loop
                                      never blocks)
```

A photo is sent from the browser to the backend as base64. The backend resizes it to a size the model's image encoder can handle, then runs an **instruction-based edit** — a plain-English sentence like *"change the cabinets to matte sage green, keep everything else unchanged"* — with no manual masking required for the core finishes. The same random seed is reused across an A/B set, so only the instruction changes between variants and the rest of the scene stays put; that is what makes the comparison fair.

The model loads once when the server starts and stays resident in GPU memory, because reloading per request is slow and risks running out of memory. Inference runs in a worker thread so the API stays responsive.

Two small JSON files — `finishes.json` and `structural.json` — hold the curated edit instructions, phrased the way Kontext responds to best (name the target, state what stays unchanged). Keeping them as data, not code, means the preset library can grow without touching the pipeline.

## Architecture at a glance

| Layer | Choice | Why |
| --- | --- | --- |
| Editing model | FLUX.1 Kontext [dev], run locally | Instruction-based editing, no masking; Qwen-Image-Edit is the commercial-friendly fallback |
| Backend | FastAPI + Pydantic | Typed request/response schemas; async endpoints |
| Inference | Loaded once at startup, run in a threadpool | Avoids reload cost and OOM; keeps the event loop free |
| Reproducibility | Fixed seed across an A/B set | Only the finish differs between variants, not the composition |
| Frontend | React + Vite + Tailwind | Fast dev loop; single-page UI |
| Image transport | base64 PNG over JSON | Simple; no multipart handling needed yet |
| Hardware target | RTX 4090, 24 GB, bfloat16 | Fits the transformer in VRAM with CPU offload for the text encoders |

## Demo

> _Before / after pair goes here once a sample run is captured._
>
> Suggested layout: original photo on the left, an A/B strip of three cabinet finishes on the right, and one structural example clearly stamped **approximate**.

## What's built

Core finishes, A/B comparison, layered edits, object removal, the experimental structural modes (move / open wall) with caveats, and a one-page spec-sheet export for handing to a contractor. The hybrid geometry-controlled mode is scoped and stubbed but not yet wired in. See `docs/project-plan.md` for milestone status and `handoff.md` for the running build log.

## Running it

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # add your Hugging Face token
uvicorn app.main:app --reload
```

The server boots even without the ML stack installed — it just reports `model_loaded: false` until the weights are present, which keeps the API testable without a GPU.

Frontend:

```bash
cd frontend
npm install
npm run dev                 # dev server proxies /api → localhost:8000
```

In production, `npm run build` emits a static bundle that FastAPI serves directly, so the whole thing runs from one `uvicorn` command.

## A note on the model

FLUX.1 Kontext [dev] is used for local development and previews. For any commercial use, Qwen-Image-Edit is the intended fallback — the pipeline wrapper is the only piece that would change.

---

*Built as a practical tool for one family's remodel and as a study in scoping an AI feature to what it can actually be trusted to do.*
