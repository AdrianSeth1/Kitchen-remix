# Feature spec — reference-image edits

**Hand this file to the local coding model.** It adds the ability to attach an example image (a cabinet style, or a specific appliance) and apply it to the user's kitchen photo. Follow the existing project conventions in `claude-code-build-spec.md` and the patterns already in `backend/app/` — match the style, don't refactor working code, keep it minimal.

The curated prompt wording lives in `backend/app/references.json` (already written). Load it the same way `structural.py` loads `structural.json` — do not hardcode the prompts.

---

## Goal

Two new edit modes, kept in separate tiers because they have different reliability:

- **Tier A — finish reference (reliable-ish).** Attach a photo of a cabinet/countertop/backsplash/floor style; apply that style to the matching surface in the kitchen. Runs on the **FLUX.1 Kontext** model already in the project.
- **Tier B — object reference (experimental).** Attach a photo of a specific appliance (e.g. a fridge); replace that object in the kitchen with one matching the reference. Runs on **Qwen-Image-Edit-2509**, a second model.

Both must be **clearly labeled** in the UI with the caveats from `references.json`.

## The model reality (read before coding)

- **FLUX.1 Kontext [dev]** does not cleanly accept two separate input images through the `diffusers` pipeline. The reliable pattern is to **stitch** the kitchen photo and the reference into one side-by-side canvas and prompt against "the left image" / "the right image", then crop the result back to the kitchen half. Tier A uses this.
- **Qwen-Image-Edit-2509** is purpose-built for multi-image edits (up to 3 inputs) and product replacement. Tier B uses this with two real inputs (`first image` = kitchen, `second image` = reference).
- **VRAM:** both models are ~20GB+ in bf16. **You cannot hold both resident on a 24GB card at once.** See the model-manager section — load one heavy model at a time and swap on demand. This deliberately revises the "load once at startup" decision in `handoff.md` for the heavy models; note it there.

> Before implementing each pipeline, **verify the current `diffusers` class names and call signatures** against the model cards — exactly as `pipeline.py` already does for Kontext. Do not assume the API from this doc.

---

## Architecture

### New files

| File | Purpose |
| --- | --- |
| `backend/app/qwen_pipeline.py` | Qwen-Image-Edit-2509 wrapper. Mirror `pipeline.py`: lazy `torch`/`diffusers` imports, `load()`, `unload()`, `is_loaded()`, `edit_with_references(image, refs, instruction, seed)`. |
| `backend/app/backends.py` | Tiny coordinator so only one heavy model is resident. `ensure(kind)` where kind ∈ {"kontext","qwen"}: if the other model is loaded, unload it first, then load the requested one. Single-user app, so a simple swap (accept the reload latency) is fine. |
| `backend/app/references.json` | **Already written.** Curated prompt templates + caveats. |

### Reused patterns (match these exactly)

- Lazy ML imports inside functions so the server boots without the ML stack (see `pipeline.py`).
- `run_in_threadpool` for all inference calls (see `routes.py`).
- base64 PNG over JSON for image transport.
- Fixed `seed` (default 42) passed through to the pipeline.
- `prepare_image()` from `pipeline.py` for sizing (longest edge ≤1024, dims rounded to multiples of 16). Reuse it; for the stitched canvas, prepare the canvas *after* stitching.
- The response-flag pattern (`approximate`, `invented_space`) — add new honesty flags, see schemas below.

### Tier A stitch helper (in `pipeline.py` or a small `stitch.py`)

```
def reference_finish(kitchen, reference, target, seed):
    1. resize both images to the same height (e.g. 768px tall), keep aspect
    2. paste side by side onto one canvas: [ kitchen | reference ]
    3. prepare_image(canvas)
    4. instruction = references["finish_reference_templates"][target]
    5. out = edit_image(canvas, instruction, seed)        # existing Kontext call
    6. crop out back to the kitchen's (left) region, at the kitchen's aspect
    7. return the crop, resized back to the original kitchen dimensions
```

Keep a record of the left-region box from step 2 so the crop in step 6 is exact.

### Model manager flow

- Keep loading **Kontext at startup** as today (it's the core path).
- On a Tier B (Qwen) request: `backends.ensure("qwen")` → unload Kontext, load Qwen, run. Leave Qwen resident.
- On any Kontext request after that (finishes, A/B, Tier A, structural): `backends.ensure("kontext")` → unload Qwen, reload Kontext, run.
- `GET /api/health` should report which heavy model is currently resident (extend the existing payload, don't break it).

---

## API

Add to `routes.py`, under `/api`. Validate inputs (bad base64 → 422) before `_require_pipeline()`, same as existing endpoints.

| Endpoint | Body | Response |
| --- | --- | --- |
| `POST /api/reference_finish` | `{ image_b64, reference_b64, target, seed }` — `target` ∈ keys of `finish_reference_templates` | `{ image_b64, style_only: true }` |
| `POST /api/reference_object` | `{ image_b64, reference_b64, target, seed }` — `target` ∈ keys of `object_reference_templates` | `{ image_b64, style_accurate: true, spec_accurate: false }` |
| `GET /api/reference-presets` | — | the contents of `references.json` (serve raw, like `/structural-presets`) |

Reject an unknown `target` with 422 and a message listing valid targets.

## Schemas (`schemas.py`)

```
class ReferenceFinishRequest(BaseModel):
    image_b64: str
    reference_b64: str
    target: str
    seed: int = 42

class ReferenceFinishResponse(BaseModel):
    image_b64: str
    style_only: bool = True

class ReferenceObjectRequest(BaseModel):
    image_b64: str
    reference_b64: str
    target: str
    seed: int = 42

class ReferenceObjectResponse(BaseModel):
    image_b64: str
    style_accurate: bool = True
    spec_accurate: bool = False
```

## Frontend

Add one component, `ReferenceTab.jsx`, rendered in the right column near `StructuralTab`. Match the existing Tailwind/stone styling.

- Two sub-sections: **Finish from a photo** (Tier A) and **Replace an appliance** (Tier B).
- Each has: a file input that reads the attached image to base64 (reuse the logic in `Upload.jsx`), a `target` dropdown (populated from `GET /api/reference-presets`), a Generate button (disabled until both the kitchen image and a reference are present), a result `<img>`, and the caveat text **from `references.json`** (`caveats.finish_reference` / `caveats.object_reference`) — do not hardcode caveat strings.
- Fetch `/api/reference-presets` once on mount for the target lists and caveats (same pattern as `StructuralTab`'s caveat fetch).
- The Tier B result must always show the `object_reference` caveat prominently (style-accurate, not spec-accurate).

No change needed to the A/B or export flow.

---

## Honest-scope labeling (non-negotiable — it's the point of this project)

- Tier A result → "Style preview from your example" + `caveats.finish_reference`.
- Tier B result → "Style-accurate, not spec-accurate" badge + `caveats.object_reference`.
- The parents' note (`docs/for-the-parents.md`) should later get one line: a photo of an appliance shows the *look*, not a promise it's that exact model or that it fits. (Out of scope for the code task — flagging for the docs owner.)

## Build order (do A first, prove it, then B)

1. **Tier A on Kontext** → verify: attach a cabinet-style photo + a kitchen photo, the output keeps the kitchen layout and only the cabinets take on the reference style, and the reference half is cropped out of the final image.
2. **`backends.py` swap manager** → verify: a Tier A (Kontext) request followed by a Tier B (Qwen) request followed by another Kontext request all succeed with no CUDA OOM; `/api/health` shows the resident model changing.
3. **Tier B on Qwen-2509** → verify: attach a fridge photo + a kitchen photo, the fridge is replaced with one resembling the reference, the rest of the room is unchanged, and the response has `spec_accurate: false`.
4. **Frontend `ReferenceTab`** → verify: both flows work end to end from the browser and show the correct caveat text pulled from `references.json`.

## Acceptance criteria (all must hold)

- Server still boots and `GET /api/health` returns 200 with the ML stack absent (lazy imports preserved).
- Only one heavy model is resident at any time; alternating requests don't OOM on 24GB.
- Unknown `target` → 422 with a helpful message; bad base64 → 422.
- Tier A final image is the kitchen aspect ratio with the reference cropped away.
- Tier B response carries `spec_accurate: false`; the UI shows the matching caveat.
- No existing endpoint or component behavior changed (run `smoke_test.py` + `npm run build`).
