# Project plan

Milestones mirror the build phases. Status as of 2026-06-27.

| # | Phase | What it covers | Status |
| --- | --- | --- | --- |
| 0 | Scaffold | Directory tree, FastAPI hello-world, Vite + React + Tailwind placeholder, `/api/health` | ✅ Done |
| 1 | Core inference | `pipeline.py` — load FLUX.1 Kontext once, `edit_image()`, fixed-seed reproducibility, CLI | ✅ Done |
| 2 | Core API | All endpoints (`/edit`, `/ab`, `/layer`, `/export`, `/remove`, `/move`, `/open_wall`), Pydantic schemas, base64 validation, boots without GPU | ✅ Done |
| 3 | Core frontend | Upload, finish selector, A/B grid, layered edit, before/after, structural tab, export UI | ⚠️ Built, had breaking bugs — fixed in the 2026-06-27 audit pass |
| 3.5 | Structural (experimental) | `remove` / `move` / `open_wall` helpers + approximate caveats surfaced in the UI | ✅ Backend done; UI wired during audit pass |
| 4 | Polish | Spec-sheet export, sample images, honest-scope README, parents' note | 🔶 In progress — README + docs done; export grouping/thumbnails aligned in 2nd fix pass |
| 5 | Hybrid stretch | Geometry-controlled rendering (ControlNet) — user supplies layout, model adds realism | ⬜ Scoped + stubbed (`hybrid.py`), not wired |
| 6 | Reference-image edits | Attach an example: Tier A finish-by-reference (Kontext stitch), Tier B object replacement (Qwen-Image-Edit-2509) | ⚠️ Built by Qwen, repaired 2026-06-27 (8 bugs, see audit). Needs GPU validation on the 4090 |

## Near-term, in order

1. **Capture a real before/after demo** → verify: a sample run produces an A/B strip and one labeled structural example; drop into README.
2. **Align the export endpoint to the spec-sheet copy** → verify: exported HTML groups finishes by category with a real preview thumbnail per row.
3. **Validate the pipeline on the 4090** → verify: `python -m app.pipeline` saves an edit and the seed-reproducibility check passes; A/B variants share composition.
4. **Wire `enable_vae_slicing` / offload fallback if OOM** → verify: a 4K phone photo edits without running out of VRAM.

## Stretch, later

5. **Hybrid geometry pipeline** → verify: given a depth/edge control image, output respects the supplied layout while finishes still apply. This is the only path to *accurate* structural change.
6. **Reference-image edits** → see `docs/feature-reference-edits.md` for the full build spec and acceptance criteria. Note: requires a model-swap manager since Kontext + Qwen-2509 can't both stay resident on 24GB.

## Legend

✅ done · 🔶 in progress · ⚠️ done but needed repair · ⬜ not started
