# Google Slides API Gotchas & Learnings

Collected from building the Helix Sprint 3 review deck (V1 + V2). These are hard-won lessons for future agents working with the `jet-slides` skill.

## Thumbnail Export

### curl export does NOT work
- `curl -L "https://docs.google.com/presentation/d/.../export/png?pageid=..."` returns **HTML error pages** (~9KB), not images.
- Google requires authentication for slide exports.
- **Always use:** `scripts/slides-cli export thumbnails --presentation <ID> --output <dir> --slides '[0,1,2]'`
- Files are saved as `slide-00.png`, `slide-01.png`, etc.
- Real PNGs are 50-200KB. If you get ~9KB files, they're HTML errors.

### Image review must use sub-agents
- **NEVER load images directly into main context** — causes "Request Entity Too Large" errors.
- Use `Task` tool with `general` subagent type, batches of 5 or fewer images.
- Sub-agents should use the `Read` tool on downloaded PNG files.
- `general` subagent works better than `explore` for image reviews.

## Transforms

### `updateShapeProperties` does NOT support `transform`
- **Wrong:** `updateShapeProperties` with `fields: "transform"` → 400 error
- **Right:** `updatePageElementTransform` with `applyMode: "ABSOLUTE"`
- Shape properties only cover fill, outline, shadow, etc. — NOT position/size.

### Transform fields — CRITICAL: omit fields you don't want to set
```json
{
  "updatePageElementTransform": {
    "objectId": "element_id",
    "applyMode": "ABSOLUTE",
    "transform": {
      "scaleY": 1.1543,
      "translateX": 300000,
      "translateY": 300000,
      "unit": "EMU"
    }
  }
}
```
**WARNING:** When a transform field is omitted from the template source, it defaults to `0`, NOT `1`. For example, vertical lines in the template have NO `scaleX` field, meaning `scaleX=0` — which zeroes out the width, making the line vertical. If you explicitly set `scaleX: 1`, the full base width is applied, creating a **diagonal line** instead. **Always compare with the template and only include fields that the template includes.**

### Repositioning elements: ALWAYS compare with template source
- **Never invent positions manually.** Always read the template's original transform values via the API and copy them exactly.
- Use the Google Slides API directly: `GET /v1/presentations/{id}/pages/{pageId}` to get full element transforms.
- The `slides-cli read slide` command returns simplified position data. For exact transforms, use the raw API.
- When repositioning multiple elements, fetch both template and target slide, diff all transforms, and apply corrections in a single batch.
- Template transforms may have fractional EMU values (e.g., `translateY: 2188873.4875`) — preserve these exactly.

### Base dimensions matter
- Template elements use base `3000000x3000000 EMU` with scale transforms.
- Creating shapes with actual pixel dimensions (e.g., `width=8544000, height=465000, scaleX/Y=1`) produces visually inconsistent elements.
- Match the template pattern: use `3000000x3000000` base + appropriate `scaleX`/`scaleY`.

### Missing vs zero transform fields
- In the Google Slides API, **omitted transform fields default to 0**.
- `scaleX: 0` on a 3000000 EMU wide element means the width component is zeroed → the element collapses to a point on the X axis. For lines, this makes them vertical.
- `scaleX: 1` on the same element means the full 3000000 EMU width is applied → for lines, this creates a diagonal from (0,0) to (3000000, height*scaleY).
- **Always check the template source.** If a field is absent, do NOT set it to 1 — leave it absent (or set it to 0 explicitly).

## Text Operations

### `set-text` strips ALL formatting — MANDATORY restoration

After every `set-text` call, ALL text formatting is lost: fontFamily, weightedFontFamily, bold, italic, fontSize, foregroundColor, underline state, and paragraph alignment. Text falls back to Google Slides defaults (Arial, not Inter). **You MUST restore formatting with `updateTextStyle` (and optionally `updateParagraphStyle`) via `edit batch` immediately after every `set-text` call.**

Failure to restore formatting is the #1 cause of broken-looking presentations. Every `set-text` must be paired with a formatting restoration batch.

#### Formatting Restoration Recipes

Use `updateTextStyle` via `edit batch` after each `set-text`. All recipes use the same JSON structure — only `fontSize`, `weight`, and `foregroundColor` vary:

```json
{"updateTextStyle": {"objectId": "<OBJ_ID>", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Inter", "fontSize": {"magnitude": SIZE, "unit": "PT"}, "weightedFontFamily": {"fontFamily": "Inter", "weight": WEIGHT}, "foregroundColor": {"opaqueColor": {"rgbColor": COLOUR}}, "underline": false}, "fields": "fontFamily,fontSize,weightedFontFamily,foregroundColor,underline"}}
```

**Charcoal RGB:** `{"red": 0.14117648, "green": 0.18039216, "blue": 0.1882353}`
**White RGB:** `{"red": 1, "green": 1, "blue": 1}`

| Element role | SIZE | WEIGHT | COLOUR |
|-------------|------|--------|--------|
| Title / heading | 19 | 700 | Charcoal |
| Body text / card body | 11 | 400 | Charcoal |
| Subtitle / subheading | 11 | 700 | Charcoal |
| Footer | 8 | 400 | Charcoal |
| Divider headline | 36 | 900 | White |
| Cover title line 1 | 36 | 900 | Charcoal |
| Cover title line 2 | 18 | 500 | Charcoal |
| Card heading | 13 | 800 | Charcoal |
| Quote text | 14 | 400 | Charcoal |
| Source / label | 7 | 400 | Charcoal |
| Attribution | 10 | 500 | Charcoal |

Use **White** for elements on JET Orange, Aubergine, or Charcoal backgrounds. Never use `themeColor: LIGHT1` — it resolves to black.

#### Paragraph style restoration

If paragraph alignment was lost (e.g., text becomes centre-aligned when it should be left-aligned), restore with:
```json
{"updateParagraphStyle": {"objectId": "<OBJ_ID>", "textRange": {"type": "ALL"}, "style": {"alignment": "START", "lineSpacing": 115, "spaceAbove": {"magnitude": 0, "unit": "PT"}, "spaceBelow": {"magnitude": 0, "unit": "PT"}}, "fields": "alignment,lineSpacing,spaceAbove,spaceBelow"}}
```

#### Batch pattern: set-text + restore formatting

Combine multiple `set-text` calls with their formatting restorations into a single batch for efficiency:
```bash
# Step 1: set-text on elements (one call per element)
scripts/slides-cli edit set-text --presentation "<PRES_ID>" --object-id "<TITLE_ID>" --text "Your title"

# Step 2: restore formatting for ALL elements touched in step 1 (single batch)
scripts/slides-cli edit batch --presentation "<PRES_ID>" --requests '[
  {"updateTextStyle": {"objectId": "<TITLE_ID>", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Inter", "fontSize": {"magnitude": 19, "unit": "PT"}, "weightedFontFamily": {"fontFamily": "Inter", "weight": 700}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 0.14117648, "green": 0.18039216, "blue": 0.1882353}}}, "underline": false}, "fields": "fontFamily,fontSize,weightedFontFamily,foregroundColor,underline"}},
  {"updateTextStyle": {"objectId": "<BODY_ID>", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Inter", "fontSize": {"magnitude": 11, "unit": "PT"}, "weightedFontFamily": {"fontFamily": "Inter", "weight": 400}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 0.14117648, "green": 0.18039216, "blue": 0.1882353}}}, "underline": false}, "fields": "fontFamily,fontSize,weightedFontFamily,foregroundColor,underline"}}
]'
```

#### White text on dark/orange backgrounds

For elements on JET Orange, Aubergine, or Charcoal backgrounds, use white foreground colour instead of charcoal:
```json
"foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}
```
Never use `themeColor: LIGHT1` — it resolves to black on most themes.

### `replaceAllText` works on groups, `set-text` prepends on group children
- For elements inside groups, use `replaceAllText` instead of `set-text`.
- `set-text` on a group child PREPENDS text instead of replacing it.

### Text color pitfall: NEVER use `themeColor: LIGHT1`
- `LIGHT1` resolves to **black** on most themes, not white.
- Always use explicit RGB: `{"rgbColor": {"red": 1, "green": 1, "blue": 1}}`.

### weightedFontFamily for Inter Black
- `bold: true` maps to weight 700 (Inter Bold).
- Inter Black is weight 900 — use `weightedFontFamily: {"fontFamily": "Inter", "weight": 900}`.

## Vertical Centering with `contentAlignment`

### When to use `contentAlignment: MIDDLE`

Applying vertical centering dramatically improves aesthetics on elements with short text in tall containers. Use `updateShapeProperties` with `contentAlignment: "MIDDLE"`:

```json
{"updateShapeProperties": {"objectId": "<ELEMENT_ID>", "shapeProperties": {"contentAlignment": "MIDDLE"}, "fields": "contentAlignment"}}
```

**Good candidates for vertical centering:**
- Quote text boxes and attribution text (short quotes in tall speech bubbles)
- Number/stat displays (single numbers like "01", "6.3", "42" in tall cards)
- Callout boxes with fill colours (month+description in timeline boxes)
- Journey/process labels (chevron labels like "Sign up", "Menu setup", "Go live")
- Severity/status boxes (short labels in coloured boxes)
- Card content titles in tall card containers (e.g., "Menu builder guide")
- Circle labels in journey/flow diagrams

**Do NOT apply vertical centering to:**
- Body text paragraphs (long text blocks should stay top-aligned)
- Page titles/headings at top of slides
- Footers
- Bullet/numbered lists
- Elements inside groups (may not respond correctly)
- Cover slide titles or divider titles (already positioned by template)
- Elements with very small containers (eff_h < 200,000 EMU)

### CRITICAL: Centering tall label boxes can cause overlap

When a label text box has a large `scaleY` (rendered height >> text content height), `contentAlignment: MIDDLE` pushes the text downward to the vertical centre of the box. If a body text element sits just below the label, the centred label text overlaps with the body text, making both unreadable.

**Example:** On NPS card slides, label boxes had `scaleY: 0.3007` (rendered height ~902,100 EMU) but contained only a single line of 13pt text. With MIDDLE alignment, the text shifted ~450K EMU down, colliding with the body text that started ~338K EMU below the label's top edge.

**Fix:** Revert to TOP alignment on label elements that sit above body text:
```json
{"updateShapeProperties": {"objectId": "<LABEL_ID>", "shapeProperties": {"contentAlignment": "TOP"}, "fields": "contentAlignment"}}
```

**Rule of thumb:** Only apply MIDDLE centering to self-contained elements (quote bubbles, stat cards, journey circles, callout boxes). Never apply it to label elements that have separate body text elements positioned directly below them.

### CRITICAL: Parallel/grid layouts must use TOP alignment

**Never apply `contentAlignment: MIDDLE` to elements in parallel/grid layouts where content length varies.** This is the most common centering mistake. When multiple elements sit side-by-side (columns, cards in a grid, timeline boxes) and contain variable-length text, MIDDLE centering causes shorter content to float downward while longer content stays near the top, destroying the shared horizontal baseline.

**Affected layout patterns:**
- Monthly timelines (12 month boxes in 2 rows)
- Stepped timelines (step boxes in parallel rows)
- 6-card grids (cards with title+description in 2x3 layout)
- Journey map finding descriptions (4+ parallel columns)
- Breadcrumb sub-step descriptions (3 parallel columns)
- Process roadmap descriptions (5 boxes below chevrons)

**The fix:** Use TOP alignment on all body/description text in parallel layouts. Number labels, chevron labels, and other single-value elements within these layouts can keep MIDDLE — only the variable-length content needs TOP.

**How to tell the difference:**
- If the element is one of several similar elements arranged horizontally or in a grid, and those elements have different amounts of text → use TOP
- If the element is self-contained (single stat number, single callout, cover title) with no adjacent elements competing for baseline alignment → MIDDLE is fine

### Batch centering recipe

Process vertical centering in batches of ~20 elements per API call:
```bash
scripts/slides-cli edit batch --presentation "<PRES_ID>" --requests '[
  {"updateShapeProperties": {"objectId": "elem1", "shapeProperties": {"contentAlignment": "MIDDLE"}, "fields": "contentAlignment"}},
  {"updateShapeProperties": {"objectId": "elem2", "shapeProperties": {"contentAlignment": "MIDDLE"}, "fields": "contentAlignment"}}
]'
```

## Shape Properties

### Outline removal
- **Works:** `"outline": {"propertyState": "NOT_RENDERED"}`
- **Fails (500 error):** Complex outline specs with `alpha: 0` on outlineFill.
- Split shape creates and styling into separate batch calls if you hit 500 errors.

### Background fill removal
- Use `"shapeBackgroundFill": {"propertyState": "NOT_RENDERED"}` to make shapes transparent.
- Don't set fill color with alpha=0 — use `propertyState` instead.

### Autofit cannot be restored via API
- `SHAPE_AUTOFIT` on `autofitType` errors when applied to duplicated slides.
- Once autofit is lost on a cloned element, it cannot be restored.
- Workaround: manually size text boxes to fit content.

## Slide Management

### `edit reorder-slides` syntax
- Uses `--slide-ids` (JSON array, plural) and `--position` (not `--index`).

### Duplicated slides get new objectIds
- After `duplicate-slide`, use `read slide` to discover new element objectIds.
- The original objectIds are preserved on the source slide.
- Template reference objectIds do NOT match duplicated slides.

### Cover images cannot be swapped via API
- The cover page images are embedded in the template and cannot be replaced programmatically.
- Use `replace-text` to update cover text instead.

## Decorative Elements

### Large accent shapes in template
- Some template slides have decorative shapes with huge base dimensions (e.g., `4425600x3414900 EMU`) positioned to extend off-canvas as design elements.
- When repositioning these, they can become massive visual problems if not scaled down or deleted.
- Always check the original template dimensions before repositioning.
- When in doubt, delete decorative elements that don't serve the new layout.

### Static chart shapes
- The numeric data template slide (index 70) has a decorative pink "area chart" — purely visual, no real data.
- These are just colored shapes, not Google Sheets-backed charts.
- Safe to delete if they don't serve the presentation content.

## Roadmap Slide (Template Index 68)

### Original structure
- 5 rows, each with `scaleY=0.1963` (height ~588900 EMU)
- Row bands use alternating fills (white, mozzarella)
- Column separators are `type="other"` (lines) with NO `scaleX` field (defaults to 0), `scaleY=1.1543`
- Grid cell blocks are rounded-corner pills with colored fills (berry, turmeric, cupcake)

### Row spacing — CRITICAL
The template rows are NOT evenly spaced. Each row has a unique Y position with variable gaps between them (~50-66K EMU). **Never calculate positions manually** — always read the template's exact transforms.

Template row band Y positions (exact values from API):
```
Row 1 (_6): translateY = 1549948.4875
Row 2 (_2): translateY = 2188873.4875
Row 3 (_3): translateY = 2844010.9875
Row 4 (_4): translateY = 3479360.9875
Row 5 (_5): translateY = 4124598.4875
```

Template initiative label positions and scaleY values (vary per row):
```
_14 (row 1): scaleY=0.1437, translateY=1628850
_16 (row 2): scaleY=0.1847, translateY=2174925   ← taller label!
_18 (row 3): scaleY=0.1437, translateY=2913012.5
_21 (row 4): scaleY=0.1026, translateY=3624850   ← shorter label!
_24 (row 5): scaleY=0.1026, translateY=4276325   ← shorter label!
```

### Column separator lines — the scaleX=0 trap
- Column separators are `STRAIGHT_CONNECTOR_1` lines with base size `3000000x3000000`.
- The template has **no `scaleX` field** — this means `scaleX=0`, which zeroes the width, making lines vertical.
- If you set `scaleX: 1` (e.g., during a transform update), the full 3M width applies, creating a **45-degree diagonal line** across the grid.
- **Fix:** Always set `scaleX: 0` (or omit it) for these separators.

### Best practice: diff-and-apply approach
When fixing roadmap positioning, use this workflow:
1. Fetch raw page data for both template and target slide via Google Slides API
2. Build a dict of `{objectId: element}` for both
3. Compare transforms for all shared elements
4. Build `updatePageElementTransform` requests only for elements that differ
5. Apply all in one batch

This ensures pixel-perfect reproduction and catches issues that visual inspection misses.

### Adding rows
- Adding a 6th row requires compressing all rows (reducing `scaleY`), which makes them look wrong.
- It's better to keep 5 rows and let the presenter add more manually.
- If you must add rows, use `scaleY≥0.165` minimum — below that, rows look compressed.

## Batch Operations

### JSON arguments
- For long JSON, write to a temp file and use `$(cat /tmp/file.json)`.
- The `presentation info` JSON output from bun has trailing commas — clean with regex.

### 500 errors on complex batches
- Split creates and styling into separate batch calls.
- Creating shapes with complex outline specs in the same batch can trigger 500 errors.
- Do creates first, then styling updates in a second batch.

## Colors Reference

| Name | RGB (0-1 scale) | Hex | Usage |
|------|-----------------|-----|-------|
| JET Orange | 1.0, 0.502, 0.0 | #FF8000 | Primary, covers |
| Charcoal | 0.141, 0.180, 0.188 | #242E30 | Text |
| Mozzarella | 0.961, 0.953, 0.945 | #F5F3F1 | Backgrounds |
| Berry | 0.949, 0.651, 0.690 | #F2A6B0 | Accents |
| Cupcake | 0.757, 0.855, 0.871 | #C1DADE | Accents |
| Turmeric | 0.965, 0.761, 0.263 | #F6C243 | Accents |
| Latte | 0.906, 0.804, 0.635 | #E7CDA2 | Accents |

## Text Box Sizing: Intentional Padding by Template Design

### Text boxes are intentionally smaller than their background shapes

A deep audit of all 177 template slides revealed that **every text box is intentionally sized smaller than its background shape**. This is a template design pattern for visual padding/margins — it is NOT a bug or misalignment.

For example, on the project context slide (template 37), the callout text box (`_544`) has a base width of 3,000,000 EMU with `scaleX=1.0` (effective: 3,000,000 EMU), while its background shape (`_538`) has `scaleX=2.36` (effective: 7,080,000 EMU). The text box is ~42% of the background width — the remaining space is intentional left/right padding.

**All 203 text boxes audited across 84 populated slides had identical size ratios to their original template values.** The Slides API does not alter text box sizes during text operations (`set-text`, `insertText`, `replaceAllText`).

### When to resize text boxes

Only resize a text box when:
1. **Text is visually overflowing or clipped** — the content you're inserting is significantly longer than the template's placeholder text, and the template's `autofitType` is `NONE` (no auto-shrink)
2. **The user explicitly requests it** — e.g., "make the text box bigger to fit more content"

Do NOT resize text boxes just because they're smaller than their background shape. That size difference is the template's built-in padding.

### Resize recipe using `updatePageElementTransform`

When you do need to resize a text box to match its background shape (or come close to it):

1. Read the background shape's transform: `scaleX`, `scaleY`, `translateX`, `translateY`
2. Set the text box's `scaleY` to match the background's `scaleY` exactly (for full height)
3. Set the text box's `scaleX` to ~80-85% of the background's `scaleX` (preserves horizontal padding)
4. Set the text box's `translateY` to match the background's `translateY` (top-align)
5. Keep the text box's `translateX` slightly offset from the background's for left padding

```json
{"updatePageElementTransform": {
  "objectId": "<TEXT_BOX_ID>",
  "transform": {
    "scaleX": 1.9088,
    "scaleY": 0.2217,
    "translateX": 1108325,
    "translateY": 3675675,
    "shearX": 0,
    "shearY": 0,
    "unit": "EMU"
  },
  "applyMode": "ABSOLUTE"
}}
```

The `update-element` CLI command also works:
```bash
scripts/slides-cli edit update-element \
  --presentation "<PRES_ID>" \
  --object-id "<TEXT_BOX_ID>" \
  --y 3675675 --width 5726400 --height 665100
```

### Preferred alternative: shorten text instead of resizing

In most cases, it's better to **rewrite the content to fit the template's intended text box size** rather than resizing the box. Resizing breaks the template's visual padding design. Only resize when the content genuinely requires more space and cannot be shortened without losing meaning.

## Additional Learnings from Template Showcase

### Card heading font weight is 800 (Extra Bold), not 700

The template card headings use Inter Extra Bold (weight 800), not Inter Bold (weight 700). When restoring formatting on card headings after `set-text`, use `weightedFontFamily: {"fontFamily": "Inter", "weight": 800}` and font size 13pt. Using weight 700 produces noticeably thinner headings that look inconsistent with the template.

### Speaker notes via set-speaker-notes

The `set-speaker-notes` command works on individual slides by slide objectId. Useful for adding presenter guidance, slide type annotations, or content source references. Notes do not appear in the presentation view — only in presenter view and print.

### Global footer replacement is the most efficient first step

After cloning the template, immediately run `replace-text` to update "Month Year" and "Title of project" across all slides before doing any individual element work. This avoids having to touch footer text on each slide individually.

### replaceAllText scope limitations

`replaceAllText` is presentation-wide — it replaces ALL occurrences of the search text across ALL slides. When multiple slides contain the same placeholder text (e.g., multiple "Lorem ipsum" blocks), all get the same replacement. This is a feature for footers/headers but a problem for unique content per slide.

**Workaround for unique content:** Use `set-text` on individual elements (by objectId) instead of `replaceAllText` when each slide needs different content for the same placeholder pattern.

### Batch request size limits

Very large batch requests (100+ operations) can hit Google API payload limits. Split into batches of 50-80 operations if you encounter 413 errors. The rate limit is ~60 requests/minute per presentation, but batch operations count as a single request regardless of how many operations they contain.

### Data validation before population

Always verify that numeric data is internally consistent before populating data-heavy slides:
- Percentages in a breakdown must sum to 100%
- Change values (e.g., "+4.2pp") must equal the difference between the values shown
- Trend indicators (up/down arrows) must match the direction of the change
- Date ranges must be consistent across slide elements (e.g., "H2" should show Jul-Dec, not Jan-Mar)

Contradictory data cannot be fixed after population because decorative arrow shapes are fixed in the template.

### Experience mapping slides (template 48, 49) — label/description overlap

The experience mapping slides have label and description text elements positioned very close together vertically. When both label and description text are populated, they overlap and become unreadable — even at reduced font sizes (8pt labels, 7pt descriptions). The only reliable fix is to **remove description text entirely** and keep only bold labels. Labels should be kept under 20 characters. Use Inter Black (weight 900) at 8pt for labels.

### Tabs slide (template 147) — only 1 editable content area

The tabs slide has 4 tab labels but only a single heading/body content area. The other 3 columns' body cells are non-text shape elements that cannot be populated via the Slides API. This is a known template limitation — treat this as a single-tab slide with 4 navigation labels.

### Company profile slide (template 146) — content positioned too low

The company profile slide has content elements (headings, body text, images) positioned at the bottom of the slide by default. After populating, the content needs to be moved upward using `update-element` with Y position adjustments. Expect to move elements up by approximately **870,000 EMU total** (multiple rounds of repositioning may be needed) to achieve proper vertical centring.

### `\u000b` (vertical tab) rendering in multi-format text elements

When using `set-text` followed by `updateTextStyle` with character ranges on elements that contain both heading and body text (separated by `\n`), the newline character sometimes renders as a literal `\u000b` (vertical tab) glyph instead of a proper line break. This produces visible `\u000b` characters in the presentation.

**Fix:** Use `deleteText` + `insertText` via batch instead of `set-text` to replace text content, then apply `updateTextStyle` with character ranges immediately after. This avoids the `\u000b` rendering issue.

```json
[
  {"deleteText": {"objectId": "<OBJ_ID>", "textRange": {"type": "ALL"}}},
  {"insertText": {"objectId": "<OBJ_ID>", "insertionIndex": 0, "text": "Heading text\nBody text here."}},
  {"updateTextStyle": {"objectId": "<OBJ_ID>", "textRange": {"type": "FIXED_RANGE", "startIndex": 0, "endIndex": 12}, "style": {"fontFamily": "Inter", "fontSize": {"magnitude": 13, "unit": "PT"}, "bold": true, "weightedFontFamily": {"fontFamily": "Inter", "weight": 800}}, "fields": "fontFamily,fontSize,bold,weightedFontFamily"}},
  {"updateTextStyle": {"objectId": "<OBJ_ID>", "textRange": {"type": "FIXED_RANGE", "startIndex": 13, "endIndex": 28}, "style": {"fontFamily": "Inter", "fontSize": {"magnitude": 11, "unit": "PT"}, "bold": false, "weightedFontFamily": {"fontFamily": "Inter", "weight": 400}}, "fields": "fontFamily,fontSize,bold,weightedFontFamily"}}
]
```

### Collage slide (template 114) — 7 empty image placeholders

The collage layout has 7 empty shape placeholders in a masonry grid. All require `insert-image` with actual image URLs to populate. Without images, the slide appears as empty grey rectangles. Only the heading text element is editable via text commands.

### Group element text replacement — `deleteText` + `insertText` vs `set-text`

For text elements inside groups, `set-text` prepends to existing content rather than replacing it. Use this batch pattern instead:

```json
[
  {"deleteText": {"objectId": "<GROUP_CHILD_ID>", "textRange": {"type": "ALL"}}},
  {"insertText": {"objectId": "<GROUP_CHILD_ID>", "insertionIndex": 0, "text": "New content here"}}
]
```

This cleanly replaces all text in the group child. Follow with `updateTextStyle` to restore formatting. Note: `replaceAllText` is presentation-wide and cannot target specific group children — use `deleteText` + `insertText` when you need to set unique text on individual group children.

### `read slide` fontInfo only reports first text run

The `fontInfo` object returned by `read slide` only shows formatting from the **first text run** in the element. If an element contains both a bold heading and normal body text (via character-range styling), `fontInfo` will only show the heading's formatting. This is a CLI limitation, not an API limitation. To verify multi-run formatting, use the raw Slides API: `GET /v1/presentations/{id}/pages/{pageId}` and inspect `textElements[].textRun.style`.

### Thumbnail export fails on world maps slide (template 155)

Google's thumbnail API returns persistent 500 errors for this slide (~30+ vector elements). Export slides individually, skipping this slide:

```python
slide_id = slides[idx]["objectId"]
url = f"https://slides.googleapis.com/v1/presentations/{pres_id}/pages/{slide_id}/thumbnail?thumbnailProperties.thumbnailSize=LARGE"
resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
img = requests.get(resp.json()["contentUrl"]).content
```

### Token refresh for long sessions

OAuth tokens expire during long presentation-building sessions. Refresh programmatically using the refresh_token from `~/.slides-cli/token.json`:

```python
import json, requests

with open("/Users/rick.vanderlinde/.slides-cli/token.json") as f:
    token_data = json.load(f)

with open("<credentials_json_path>") as f:
    creds = json.load(f)["installed"]

resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "refresh_token": token_data["refresh_token"],
    "grant_type": "refresh_token"
})
token_data["access_token"] = resp.json()["access_token"]
with open("/Users/rick.vanderlinde/.slides-cli/token.json", "w") as f:
    json.dump(token_data, f, indent=2)
```

---

## Known Limitations

### Cover and closing slide backgrounds
Cover slides (0-12) and closing slides (85, 176) have background colours/images baked into the template. Each cover option uses a different colour/image combination — these are design choices, not value-stream restrictions. Pick the cover that visually suits the presentation. Background colour CAN be changed via `updatePageProperties` with `pageBackgroundFill.solidFill.color`, but this only changes the solid fill — it does NOT replace the decorative food/product images. To get a different cover image, you must rebuild the deck from the template with the desired cover slide kept.

### Cover stream name badge overflow (slides 0-12)
Each cover slide has a dark badge/tag element displaying the stream name (e.g. "Research", "Logistics"). The badge background shape has a fixed base width of 3,000,000 EMU with a `scaleX` transform that controls the rendered width. Different template covers have different `scaleX` values to accommodate different text lengths:

| Badge Text | Chars | scaleX |
|-----------|-------|--------|
| "Writing" | 7 | 0.241 |
| "Fintech" | 7 | 0.2491 |
| "Ventures" | 8 | 0.2773 |
| "Logistics" | 9 | 0.2773 |
| "Research" | 8 | 0.3138 |
| "Partner UX" | 10 | 0.3435 |
| "Localisation" | 12 | 0.3508 |
| "Customer UX" | 11 | 0.3768 |
| "Design System" | 13 | 0.4164 |
| "Service Design" | 14 | 0.4164 |
| "Product & Tech" | 14 | 0.44 |
| "Content Operations" | 18 | 0.5191 |
| "Creation & Compliance" | 21 | 0.6189 |
| "Customer and Partner Care" | 25 | 0.6946 |

Badge font must be Inter Bold (weight 700), 11pt, white text on charcoal fill. `autofitType: NONE` — the badge does NOT auto-shrink text. When replacing badge text, calculate the correct `scaleX` from this table (interpolate for unlisted lengths) and set it via `updatePageElementTransform` in the batch request. Keep badge text under 18 characters.

**Badge scaleX fix recipe:**
```json
{"updatePageElementTransform": {"objectId": "<BADGE_ID>", "transform": {"scaleX": 0.44, "scaleY": 0.0958, "translateX": 452400.0475, "translateY": 1259425, "unit": "EMU"}, "applyMode": "ABSOLUTE"}}
```
The `scaleY`, `translateX`, `translateY` values are the same across all covers — only `scaleX` varies.

### Charts and graphs cannot be populated via API
The Google Slides API cannot inject data into chart objects. Slides with chart placeholders (e.g., slide 69) show empty or placeholder data. For data visualisation, use numeric data slides (slide 70) or graphs with headings (slide 67) where you populate text elements with numbers. Alternatively, create charts externally and insert them as images using `edit insert-image`.

### Group elements hide nested text
Group elements (`type: "group"` with `children` array) contain nested text that `set-text` cannot replace properly — it prepends instead. See § "Group element text replacement" above for the correct `deleteText` + `insertText` pattern. Use `replaceAllText` for presentation-wide replacements. Affects call-out slides (59-62), some card layouts, and journey/process flows.

### Process roadmap (slide 152) has only 4 description boxes
Despite showing 5 steps, only the first 4 steps have editable description text boxes. The 5th step has a label but no description area.

### Graphs — numeric data (slide 70) has only 2 slots
Only 2 large-number display areas are available, not 4.

### Tabs slide (slide 147) has limited editable areas
Has 4 tab labels but only a single heading/body content area. See `template-guide.md` § "Section 42: Page with Tabs" for details.

### Thank You slide (176) vs Thanks slide (85)
Slide 176 has only "Thank you" text — no contact info placeholders. For presenter contact details, use slide 85 which has name, role, and email placeholders.

### Text alignment in cards
Card text alignment (left vs center) is inherited from the template. Some card layouts have center-aligned text by default. To change alignment, use `edit batch` with `updateParagraphStyle` requests.

### Replace-text ordering
When using `edit replace-text` with multiple replacements, earlier replacements can modify text that later replacements need to match. Always order replacements from most-specific (longest) to least-specific, or use `set-text` on individual elements instead.

### Duplicate group content after replaceAllText
`replaceAllText` is presentation-wide — when multiple group elements share identical placeholder text, all get the same value. Use unique placeholders per card, or accept shared content. See § "Group element text replacement" above for per-element alternatives.

### Text boxes are intentionally smaller than background shapes
This is by design — see § "Text Box Sizing: Intentional Padding by Template Design" above for the full explanation and resize recipe. Prefer shortening text over resizing boxes.

### Process roadmap date label overlap (slide 152)
The first date label text box on the process roadmap is only 250x250 EMU (extremely small). Any text placed in it overflows and overlaps with the first chevron label (e.g., "Discovery"). This is a template structural issue — the text box cannot be resized via the API.

### Decorative shape elements cannot be modified
Arrow indicators, severity badges, and decorative shapes have fixed appearance. Content narratives must match the template's fixed decorative elements (e.g., arrow direction must match the data trend).

### Content grid card (slide 73) group structure
Uses group elements for some cards with hidden text. Always use `replaceAllText` to clear template placeholders after duplicating. See § "Group element text replacement" above.

### 6-card slides (74, 75) have a floating 7th element
Template artefact below the main 2x3 grid. Delete with `edit delete-element` if it causes visual issues.

### Breadcrumb slides (77-80) footer clipping
Footer text box is partially hidden behind the left panel boundary. Keep project titles very short. Slides 79/80 may have orphan empty bullet points ("●") in the side panel.

### 1-column subtitle slides (94, 95) narrow footer
These slides have a narrower footer text box than other templates. Long project titles in the footer wrap to two lines, which looks unprofessional. Keep project titles to ~30 chars for these slide types.

### Competitive comparison (72) — narrow columns
Numeric values with 2+ chars break across lines. Apply `update-text-style --size 14` to all score cells after populating. Use single-char scores ("3", "A+").

### Call-out v2/v3 (60, 61) phone mockup
Phone frame appears blank without `insert-image`. Prefer call-out v1 (59) or short/medium/long (82-84) if no screenshot is available. See `template-guide.md` § "Section 17: Call-out Text".

### Split with icons (141-144) — non-editable icon shapes
The 3 icon slots are empty shapes, not image placeholders — cannot be replaced via API. Focus on text labels and descriptions.

### 3-card with graph (154) — graph area is a text shape
The "graph" area on this slide is a simple text shape containing "Insert graph here", NOT a linked chart object. It has only 2 stat cards (not 3) on the right side. To add a graph, create one externally and insert it as an image using `edit insert-image`, or replace the placeholder text with a text-based data summary.

### 7-card page (113) — empty grid cell
This slide uses a 4x2 grid layout with 7 cards, leaving the bottom-left cell intentionally empty. This is by design — do not try to fill the 8th cell.

### Results slide (153) — table element
This slide contains a table element for data display. Table cell contents need the `batch` API with table-specific requests (`insertText`, `deleteText` scoped to table cells). The standard `set-text` command does not work on table cells. If the table contains placeholder values like "xx%", use `replaceAllText` via batch to replace them.

### Timeline 5-phase (151) — shared text elements
Each phase block has a single text element containing both the phase label and description separated by a newline. Use `set-text` with `\n` to set both at once (e.g., `"Discovery\nStakeholder interviews and current-state mapping."`).

### Numeric data slide (70) — text overlap risk
Hero numbers must be 2-3 chars max. Y-axis label boxes (`_496`-`_501`) are single-character wide — multi-digit numbers stack vertically (template limitation). Y-axis order is top-to-bottom (100, 80, 60, 40, 20, 0).

### Template stock images cannot be changed via text commands
See § "Cover images cannot be swapped via API" above. For non-cover slides, use `edit insert-image` to replace baked-in photos.

### Graph placeholder (69) — 2x2 grid structure
This is a 2x2 grid of graph zones, NOT a single chart area. Each zone has a Title+Description group pair (use `replaceAllText`) and an empty rectangle for `insert-image`.

### Video clips (53, 54) — no video embedding
Video placeholder frames cannot be populated via API. Use `insert-image` for still frame screenshots.

### Collage (114) — 7 empty image placeholders
All 7 placeholders require `insert-image`. Only the heading is text-editable. See `template-guide.md` § "Section 34: Collage".

### Call-out v4 (62) — curly quote matching
The speech bubble group on slide 62 has placeholder text wrapped in curly quotes (`\u201c`/`\u201d`). When using `replaceAllText`, do NOT include the curly quotes in the `containsText` search string — they are separate characters that wrap the placeholder but are not part of the match.

### World maps divider (155) — decorative shapes
~30+ decorative shape elements forming a world map. Only the heading text is editable. Thumbnail export returns 500 errors for this slide — skip it when batch-exporting.

### Links & decks (81) — title length causes text overlap
Each link entry has a title text box above a date text box with a fixed vertical gap (~200K EMU). If the title wraps to 2 lines, the second line overlaps the date text, making both unreadable. Keep link titles to **20 characters max** to prevent wrapping.

### 6-card numbered long (76) — centre floating card
7th floating card is centre-aligned by design, with a stock image above it (use `insert-image` to replace).

### Three numbered points (39) — centre-aligned body text
The three content columns on this slide have centre-aligned body text by default (inherited from the template). This differs from the general left-alignment rule. Keep body text per column to ~200 characters.

### Baked-in stock images repeat when duplicating slide types
Grid slides (73-76), card pages (105-113), and some dividers contain stock images that repeat on duplicates. Use `insert-image` to replace on duplicates, or choose a slide type without baked-in images.

---

## Troubleshooting

### Auth expired
```
slides-cli auth login --credentials conf/client_secret_602299916251-7aodem5aquraoo8m9goeepn3ugi5ok22.apps.googleusercontent.com.json
```

### Permission denied on template
The template must be accessible to the authenticated user. The template ID is: `1M-8jgsBKitaL6pkVg_78DcoFm__9_MoEmmkpazKkv9k`

### Element objectIds not matching
After deleting or duplicating slides, objectIds on existing slides remain stable. Duplicated slides get new objectIds. Use `read slide` to discover objectIds on duplicated slides.

### `set-text` strips all text formatting
See § "`set-text` strips ALL formatting — MANDATORY restoration" above for the full recipe and parameter table. Key points for troubleshooting:
- Cover titles need per-line formatting: Line 1 is Inter Black 900/36pt, Line 2 is Inter Medium 500/18pt
- Use charcoal RGB for light covers, white RGB for JET Orange/Aubergine covers
- Never use `themeColor: LIGHT1` — it resolves to black
- Use `weightedFontFamily` with `weight: 900` for Inter Black — `bold: true` only gives 700

### Text replacement not working
- `replace-text` does global find-and-replace across all slides — useful for footers and repeated placeholders
- `set-text` targets a specific element by objectId — clears existing text and sets new text (but strips formatting — see above)
- Use `\n` for line breaks in `--text` arguments — the CLI auto-converts to real newlines
- For partial text updates within an element, use `edit batch` with `insertText` and `deleteText` requests

### Group elements and hidden placeholders
`set-text` prepends on group children instead of replacing. See § "Group element text replacement" above for the correct `deleteText` + `insertText` and `replaceAllText` patterns. Always check group children for hidden placeholder text on call-out slides (59-62).

### Text overflowing boxes
Content exceeds the template's designed text box size. Shorten the text to fit, or see § "Text Box Sizing" above for the resize recipe. Check character limits in `references/template-guide.md` (element capacity tables per slide type).

### Timeline slides (47, 151, 152) — vertical overlap
Timeline slides alternate items above and below a horizontal line. **Above-line items** place the description text ABOVE the label — if the description is too long, it pushes down into the label. Keep above-line descriptions under 60 characters. Below-line items have more room (~80 chars).

### Highs/Lows slides (55, 56) — right panel overlap
The right panel has a heading and a bullet list. The heading text box and bullet list text box are positioned close together. If the heading wraps to 2 lines, it overlaps the first bullet. Keep the right-panel heading under 20 characters.

### Long JSON arguments
For commands with long JSON arguments, write the JSON to a temporary file and use command substitution:
```bash
slides-cli edit delete-slides --presentation "<ID>" --slide-ids "$(cat /tmp/slide-ids.json)"
```
