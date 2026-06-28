# Contractor spec sheet — copy & layout

Defines the content and layout for the app's export feature (`POST /api/export`). The goal: a clean one-page summary a homeowner can hand a contractor or supplier, listing chosen finishes by category with a thumbnail next to each. It is a starting point for a quote, not a construction document.

## Page layout (top to bottom)

1. **Title bar** — project title + generated date.
2. **Original photo** — one image, captioned, so the contractor sees the starting kitchen.
3. **Selected finishes, grouped by category** — each category is a labeled section; within it, one row per finish: thumbnail on the left, finish details on the right.
4. **Final composite** (optional) — the combined preview, if the homeowner generated one.
5. **Footer disclaimer** — what these previews are and aren't.

## Copy

**Title:** `Kitchen Remix — Finish Spec Sheet`

**Subtitle / meta line:** `Prepared for contractor review · Generated {date}`

**Original section heading:** `Current kitchen`
**Original caption:** `Starting photo — finishes below are applied to this room.`

**Finishes section heading:** `Selected finishes`

**Category headings** (only shown if that category has a selection): `Cabinets` · `Countertops` · `Backsplash` · `Flooring` · `Paint`

**Per-finish row:**
- Thumbnail (the generated preview of that finish).
- **Finish name** in bold (e.g. *Matte Sage Green*).
- One line of plain detail beneath it (e.g. *Cabinets — matte sage green painted finish*).

**Final composite heading:** `Combined preview`
**Final composite caption:** `All selected finishes shown together (approximate).`

**Footer disclaimer:**
> These are AI-generated previews of color and material only. They are not measured drawings. Colors vary by screen, lighting, and product batch — confirm against physical samples before ordering. Any layout or structural changes shown elsewhere are approximate and not included here.

## Notes for implementation

- **Group by category.** The current `/api/export` endpoint renders all finishes in one flat grid. This copy spec groups them under category headings, which reads better for a contractor scanning for "what countertop did they pick." Worth aligning the endpoint to this.
- **Thumbnails need a real preview image per finish.** Each row's thumbnail should be the generated A/B result for that finish, not the original photo. (See the audit note on the export data flow.)
- **Print-friendly.** Keep it single-column on print, generous margins, no dark backgrounds — it should look right on white paper. The existing endpoint's print CSS is a good base.
- **One page where possible.** If selections overflow, let categories break naturally rather than forcing everything onto one sheet.
