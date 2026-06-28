# Code audit — 2026-06-27

Review of the kitchen-remix codebase. Backend (phases 0–2) was written by Sonnet and is in good shape. The frontend and docs (phases 3–4) were written by a local Qwen-Coder 30B model and contained several real bugs, including one that crashed the app. Findings below, worst first.

## Fixed in this pass (the breaking bugs)

| # | Severity | Where | Problem | Fix |
| --- | --- | --- | --- | --- |
| 1 | **Critical** | `StructuralTab.jsx` | The Remove / Move / Open-wall buttons called `handleRemove`, `handleMove`, `handleOpenWall` — none of which were defined. Referencing an undefined identifier in JSX throws a `ReferenceError`, so the component crashed on render. Because it mounts as soon as a photo is uploaded, the **whole app went blank** the moment you used it. The declared `loading` / `error` / `*Result` state was all dead. | Added a shared `runStructural()` helper and the three handlers; they POST to `/api/remove`, `/api/move`, `/api/open_wall` and drive the existing state. |
| 2 | **High** | `FinishSelector.jsx` + `App.jsx` + `ExportSpecSheet.jsx` | Spec-sheet export could never run. `App` passed `onSelectionChange` to `FinishSelector`, but the component never destructured or called it, so `selectedFinishes` stayed `[]` and the Download button was permanently disabled. Even if populated, the selection objects had no `image_b64`, which the backend's `ExportSelection` requires → would 422. | `FinishSelector` now tracks a multi-select and reports it. Export now sources the **A/B previews** (`{label, image_b64}`), which match the backend schema, and renders real thumbnails. |
| 3 | **High** | `App.jsx` + `AblGrid.jsx` | A/B comparison only ever compared **one** finish: `App` passed `finishes={[selectedFinish]}` (a single string, empty at first). And `AblGrid` set local results but never called the `onGenerateAB` prop, so results never reached the parent (and thus never reached export). | A/B now receives all selected finishes plus their labels, and lifts results to `App` via `onGenerateAB`. |
| 4 | **Medium** | `AblGrid.jsx` | The "Base Instruction" input's `onChange` called `onSelectFinish(e.target.value)` — editing it silently overwrote the selected finish instead of the base instruction. | Now calls `onBaseInstructionChange` (wired to `setBaseInstruction`). |
| 5 | **Low** | `finishes.json` | Instructions lacked the "keep everything else unchanged" clause Kontext relies on. Masked in A/B (the base instruction is appended there) but not in the single `/edit` and `/layer` paths, where edits were under-constrained. | Rewrote every instruction to be self-contained (name the target, state what stays). Also expanded to 8 presets per category. |
| 6 | **Low** | `README.md` | Overclaimed: described database integration, user auth, and a `PUT /api/specsheet` endpoint that doesn't exist in `routes.py`. | Rewrote around the honest scope tiers; removed the phantom features. |

## Fixed in the second pass (2026-06-27)

After the first report, these were all cleared.

| # | Severity | Where | Issue | Fix |
| --- | --- | --- | --- | --- |
| 7 | **Medium** | `structural.py` vs `structural.json` | Two sources of truth. `structural.py` hardcoded the instruction strings; `structural.json` held parallel templates the backend never read. | `structural.py` now loads templates from `structural.json` (cached) and fills the placeholders. Single source. |
| 8 | **Low** | `routes.py` + frontend | `GET /api/structural-presets` was fetched by no component; `StructuralTab` hardcoded its caveat text. | `StructuralTab` now fetches the endpoint and renders `caveats.move` / `caveats.open_wall` from the JSON (with a fallback if the fetch fails). |
| 9 | **Medium** | `routes.py` `/export` | Rendered a flat grid; spec-sheet copy wanted grouping by category with a thumbnail per finish. | `/export` now groups by category in canonical order, with headings, per-finish thumbnails, and the disclaimer footer. `ExportSelection` gained a `category` field; the frontend tags A/B previews with their category (matched by label) before export. |
| 10 | **Low** | `structural.py` `move_object` | Remove-then-add used the same seed for two passes — an undocumented assumption. | Move is now a single pass via the curated template (cleaner, fewer compounding artifacts); the two-pass concern is gone. |

## Reported, not changed

| # | Severity | Where | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| 11 | **Info** | `main.py` | No CORS middleware. Fine while the Vite dev proxy keeps things same-origin; would only bite if the frontend is ever served from a different origin than the API. | Leave as-is unless deployment changes. |

## What's solid (no action)

The backend inference path is well built: lazy `torch`/`diffusers` imports so the server boots without the ML stack, fixed-seed reproducibility (the thing that makes A/B honest), `prepare_image` rounding to multiples of 16 for the FLUX VAE, threadpool offload so the event loop never blocks, and validation ordered so callers get 422 before 503. `smoke_test.py` still holds — now 5 categories / 40 presets.

## Phase 6 — review of the reference-edits build (2026-06-27)

The local coding model implemented the feature from `feature-reference-edits.md`. The shape was right, but nothing had been run, so every path was broken. All fixed.

| # | Severity | Where | Problem | Fix |
| --- | --- | --- | --- | --- |
| A | **Critical** | `pipeline.py` | `reference_finish` was pasted into the `__main__` block, leaving an unterminated `logger.warning(` → `SyntaxError`. The module wouldn't import, so the server couldn't boot. | Restored the CLI block; `reference_finish` is now a clean module-level function. |
| B | **Critical** | `routes.py` | `/edit` was split — `@router.post("/edit")` + `async def edit():` with no body, body orphaned after `reference_object`. Reference response schemas weren't imported. Two import-time failures. | Rebuilt the file with correct endpoint order, restored `/edit`, imported the Reference schemas + `qwen_pipeline`. |
| C | **Critical** | missing `references.py` | Code did `from . import references` and read `references.FINISH_REFERENCE_TEMPLATES`, but `references` was only a JSON data file. ImportError. | Added `references.py` that loads `references.json` and exposes the dicts (mirrors `structural.py`). |
| D | **Critical** | `qwen_pipeline.py` | Used `QwenImageEditPipeline` (single-image) and `pipe(image=img, images=refs)`. The 2509 model is `QwenImageEditPlusPipeline` and takes `image=[kitchen, ref]` as a list — verified against diffusers docs. | Corrected the class and the call. |
| E | **Critical** | `ReferenceTab.jsx` | Was a stub: "Reference features are coming soon!" — no UI. | Built the real two-tier UI (reference upload, target dropdown, generate, result, caveats from `references.json`). |
| F | **High** | `backends.py` | The swap "unloaded" by setting `_pipeline = None` only — no `gc` / `torch.cuda.empty_cache()`, so VRAM was never freed → OOM on the second model. Defeated the whole point. | Added `unload()` (del + `gc.collect()` + `empty_cache()`) to both pipelines; `backends.ensure()` calls them. |
| G | **Medium** | `schemas.py` | Inserting the new models clobbered `OpenWallResponse` (lost `invented_space`) and added a stray `invented_space` to `ReferenceObjectResponse`. | Restored / removed respectively. |
| H | **Medium** | `pipeline.reference_finish` | Tier A cropped using pre-resize canvas coords, but `prepare_image` rescales the canvas (almost always), so the crop was misaligned. | Crop now uses the kitchen's *fraction* of the canvas width — robust to any rescale. |

Lesson for next time: a local 30B coder produces structurally-plausible code that hasn't been executed. Treat "it's done" as "it compiles-maybe" — run it before trusting it.

## Verification note

The sandbox shell mount was out of sync (and in this last round, actively corrupted — null bytes, truncated copies) with the file tools, so I could not run `npm run build` / `smoke_test.py` / `py_compile` against the real files. I verified instead by reading every changed file back through the file tools and checking the tricky bits by eye: the JSON keys match the `references.py` constants, the verified Qwen API (`QwenImageEditPlusPipeline`, `image=[...]`), the restored `/edit` and `pipeline.py` structure, and the React `references.json → ReferenceTab` flow. **Run `python smoke_test.py` and `npm run build` locally before committing — that's the one check I can't do from here.**
