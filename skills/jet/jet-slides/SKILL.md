---
name: jet-slides
description: Generate Google Slides presentations for JET (Just Eat Takeaway.com) using brand templates, visual identity, and brand voice guidelines. Use when creating slide decks, presentations, pitch decks, research readouts, project updates, quarterly reviews, or any Google Slides content for JET. Triggers on requests to create presentations, make slides, build a deck, prepare a readout, or generate Google Slides output for JET-related topics. This skill creates actual Google Slides presentations via the Slides API — it does NOT apply to PowerPoint files, matplotlib/chart generation, PDF reports, Confluence pages, markdown documents, README files, Slack messages, React components, image carousels, or any non-Google-Slides output. If the user wants a presentation or deck (not a document, report, or code), use this skill.
metadata:
  owner: ai-platform
---

# JET Slides Skill

Create professional Google Slides presentations for JET (Just Eat Takeaway.com) using the official Product & Tech template, brand voice, and visual identity guidelines.

## CRITICAL: Image / Thumbnail Review

NEVER read or open slide thumbnail images (PNGs, JPGs, etc.) directly into the main conversation context. They are large and will cause "Request Entity Too Large" errors.

When reviewing slide thumbnails or any images:
- Always delegate to sub-agents using the Task tool
- Process images in batches of **5 or fewer** per sub-agent
- Have the sub-agent summarize findings in text; never pass images back to the main context

## Overview

This skill clones the JET Product & Tech presentation template, selects appropriate slide types for the content, populates them with branded copy, and returns a shareable Google Slides link. Every presentation uses the Inter font family and JET brand colours.

## Prerequisites

The `slides-cli` tool is bundled at `scripts/slides-cli`. It installs dependencies on first run and executes the TypeScript source directly with `bun`.

### Authentication

Check auth status first:

```bash
scripts/slides-cli auth status
```

If not authenticated, run:

```bash
scripts/slides-cli auth login --credentials conf/client_secret_602299916251-7aodem5aquraoo8m9goeepn3ugi5ok22.apps.googleusercontent.com.json
```

This opens a browser for Google OAuth2. The token is stored at `~/.slides-cli/token.json`.

**Required scopes:** `https://www.googleapis.com/auth/presentations`, `https://www.googleapis.com/auth/drive`

## Workflow

Follow these steps for every presentation request:

### Step 1: Plan the Deck

Based on the user's request, plan which slides to include. A well-formed JET presentation follows this structure:

1. **Cover page** (1 slide) — choose from slides 0-12 based on topic/aesthetic preference
2. **Contents page** (optional, for 10+ slide decks)
3. **Section divider** — for breaking up sections
4. **Context/intro slides** — background, objectives
5. **Executive summary** — key takeaways
6. **Content slides** — data, insights, quotes, etc.
7. **Section dividers** between major sections
8. **Conclusion or Summary**
9. **Thanks/closing** — slide 85 (with contact info) or slide 176 (simple "Thank you")

**Cover slide selection:** The template has 13 cover options (slides 0-12), each with different colour/image combinations. These are examples labelled by value stream but can be used for any topic — just replace the placeholder text. Pick the cover that best suits the visual tone of the presentation.

**Closing slides:** Slide 85 ("Thanks") includes contact info placeholders. Slide 176 ("Thank you") is a minimal closing with just text. Their background colours are baked into the template and vary.

### Step 2: Clone the Template

```bash
scripts/slides-cli create from-template \
  --template "1M-8jgsBKitaL6pkVg_78DcoFm__9_MoEmmkpazKkv9k" \
  --title "Your Presentation Title"
```

Returns JSON with `presentationId` and `url`. Save the `presentationId` for all subsequent commands.

### Step 3: Delete Unwanted Slides

The template has 177 slides. You must delete all slides you don't need.

**Always delete these template-internal slides** (objectIds):

```
Template-internal slides to always delete:
- Slide 13: g316222bded8_0_194 (template TOC)
- Slides 28-34: g33965faa38a_3_0, g2529b319071_0_897, g3150fa87b39_0_1, g31c47e133ce_0_4, g2529b319071_0_914, g329ad47a42a_0_464, g31669fcce71_1_17
- Slides 157-160: g2529b319071_0_4725, g2529b319071_0_4634, g2529b319071_1_158, g254b492889a_2_45
- Slides 161-175: g32dba28f83f_0_208, g32dba28f83f_0_1964, g32dba28f83f_0_2803, g32dba28f83f_0_2814, g32dba28f83f_0_2823, g32dba28f83f_0_792, g32dba28f83f_0_1241, g32dba28f83f_0_1215, g32dba28f83f_0_2407, g32dba28f83f_0_3168, g339b9ac78be_6_29, g32dba28f83f_0_3207, g3341416f5e6_0_39, g339b9ac78be_6_2, g339b9ac78be_7_17
```

Then delete all unused slide types. Keep only the cover page for the right value stream (delete the other 12 covers), the slides you plan to use for content, and the closing slide.

Use `delete-slides` with a JSON array of objectIds:

```bash
scripts/slides-cli edit delete-slides \
  --presentation "<PRES_ID>" \
  --slide-ids '["g316222bded8_0_194", "g33965faa38a_3_0", ...]'
```

**Important:** Delete slides in a single batch call. The API uses objectIds (not indices), so ordering doesn't matter.

### Step 4: Arrange Slides (if needed)

To duplicate a slide (e.g., to create multiple content slides of the same type):

```bash
scripts/slides-cli edit duplicate-slide \
  --presentation "<PRES_ID>" \
  --slide-id "<OBJECT_ID>" \
  --position <0-BASED-INDEX>
```

### Step 5: Populate Content

#### Option A: Replace placeholder text globally

For placeholders that appear across slides (e.g., footer, project name):

```bash
scripts/slides-cli edit replace-text \
  --presentation "<PRES_ID>" \
  --replacements '[{"placeholder":"Month Year","value":"March 2026"},{"placeholder":"Title of project","value":"Q1 Logistics Review"}]'
```

#### Option B: Set text on a specific element

When you know the exact objectId of a text element:

```bash
scripts/slides-cli edit set-text \
  --presentation "<PRES_ID>" \
  --object-id "<ELEMENT_ID>" \
  --text "Your new content here"
```

Use `\n` in the text string for line breaks — the CLI converts `\n` to actual newlines automatically. Example:

```bash
scripts/slides-cli edit set-text \
  --presentation "<PRES_ID>" \
  --object-id "<ELEMENT_ID>" \
  --text "Project name\nValue Stream"
```

**CRITICAL: `set-text` strips ALL formatting.** After every `set-text` call, you MUST restore formatting with `updateTextStyle` via `edit batch`. Without this, text falls back to Arial. See **`references/slides-api-gotchas.md`** § "Formatting Restoration Recipes" for copy-paste JSON templates per element type, and **`references/visual-identity.md`** § "Type Hierarchy for Slides" for the full font/size/weight spec table.

**Key rules:** Always include `"underline": false`. Use white text on JET Orange/Aubergine backgrounds. Never use `themeColor: LIGHT1`. Batch all restorations into a single `edit batch` per slide.

#### Option C: Batch update (advanced)

For complex operations, send raw Google Slides API requests:

```bash
scripts/slides-cli edit batch \
  --presentation "<PRES_ID>" \
  --requests '[{"replaceAllText":{"containsText":{"text":"Lorem ipsum","matchCase":false},"replaceText":"Actual content"}},{"deleteObject":{"objectId":"someId"}}]'
```

### Step 6: Read Slide Structure

To discover element objectIds on a slide for targeted text updates:

```bash
scripts/slides-cli read slide \
  --presentation "<PRES_ID>" \
  --index <0-BASED-INDEX>
```

This returns all elements with their objectIds, types, sizes, and text content. Group elements are returned as `type: "group"` with a `children` array containing nested element objectIds and text.

### Step 6b: Move or Resize Elements (Optional)

To reposition or resize a page element:

```bash
scripts/slides-cli edit update-element \
  --presentation "<PRES_ID>" \
  --object-id "<ELEMENT_ID>" \
  --x <EMU> --y <EMU> --width <EMU> --height <EMU>
```

All values are in EMU (English Metric Units). 1 inch = 914400 EMU. Only specify the properties you want to change.

### Step 6c: Update Text Style (Optional)

To change font, size, colour, or weight on text elements:

```bash
scripts/slides-cli edit update-text-style \
  --presentation "<PRES_ID>" \
  --object-id "<ELEMENT_ID>" \
  --font "Inter" --size 11 --bold true --color "#242e30"
```

Optional `--start` and `--end` parameters apply styling to a character range only.

### Step 7: Share the Presentation

Share with a specific user:

```bash
scripts/slides-cli share user \
  --presentation "<PRES_ID>" \
  --email "user@justeattakeaway.com" \
  --role writer
```

Share with the entire JET domain:

```bash
scripts/slides-cli share domain \
  --presentation "<PRES_ID>" \
  --domain "justeattakeaway.com" \
  --role reader
```

### Step 8: Return the Link

Always return the presentation URL to the user. The URL format is:
`https://docs.google.com/presentation/d/<PRES_ID>/edit`

---

## Template Slide Reference

The template (`1M-8jgsBKitaL6pkVg_78DcoFm__9_MoEmmkpazKkv9k`) contains 177 slides. For the full catalogue with objectIds, slide types, cover colour/image mappings, and cover title population recipes, see **`references/template-guide.md`**.

Key categories: Cover pages (0-12), Dividers (14-27, 35, 93, 104, 145), Contents (36), Project context (37-39), Executive summary (40), Quotes (43-44), Three points/Insights (50-52), Cards (105-113), Grids (73-76, 86-98), Split pages (99, 125-139), Timeline/Roadmap (68, 151-152), Conclusion/Summary (149-150), Thanks/Closing (85, 176).

**Always delete template-internal slides** (13, 28-34, 157-160, 161-175) — see Step 3 for objectIds. For template images and their suitability per topic, see the Template Image Guide in `references/template-guide.md`.

---

## Recommended Slide Combinations by Presentation Type

### Research Readout (10-15 slides)
1. Cover (Research — slide 5)
2. Contents (36)
3. Divider: "Background" (14)
4. Project context (37 or 38)
5. Executive summary (40)
6. Divider: "Findings" (14, duplicated)
7. Three points / insights (50 or 51) — duplicate for multiple findings
8. Quotes (43 or 44)
9. The Highs (56) + The Lows (55)
10. Call-out text for key insight (59)
11. Divider: "Recommendations" (14, duplicated)
12. 3-point conclusion (115)
13. Thanks (85)

### Quarterly Business Review (8-12 slides)
1. Cover (matching value stream)
2. Executive summary (40)
3. Divider: "Performance" (14)
4. Graphs / data slides (67, 70, or 71)
5. Content grid with initiatives (73 or 75)
6. Divider: "Roadmap" (14, duplicated)
7. Roadmap Now/Next/Later (68)
8. Timeline (151 or 152)
9. Conclusion (150)
10. Thanks (176)

### Project Update (6-8 slides)
1. Cover (matching value stream)
2. Project context (37)
3. Three points — what we did (50)
4. Results (153) or Graphs (70)
5. Call-out text — key learning (82)
6. Summary (149) or 3-point conclusion (115)
7. Thanks (85)

### Strategy / Pitch Deck (10-15 slides)
1. Cover (matching value stream)
2. Contents (36)
3. Intro (41)
4. Divider: "The Opportunity" (14)
5. Split page with image (99 or 126)
6. Three points (50)
7. Divider: "Our Approach" (14)
8. Card pages (111 or 112) — solution components
9. Timeline / roadmap (68 or 152)
10. Divider: "Expected Impact" (14)
11. Graphs (70)
12. Conclusion (150)
13. Thanks (176)

---

## Brand Voice Rules

Apply JET's **Bold, Relatable, Motivating, Optimistic** voice when writing slide content. Full rules in **`references/brand-voice.md`**.

**Critical rules to always follow:**
- **Sentence case everywhere** — capitalise only the first word and proper nouns. Never use Title Case. This is the #1 brand violation.
- **Never underline text** unless it is a clickable hyperlink.
- **Text length limits** — template text boxes have fixed sizes. Exceeding limits causes overflow. See element capacity tables in **`references/template-guide.md`** per slide type.
- **Slide selection** — match content count to slide variant (e.g., 2 items → 2-card slide, not 3-card with one blank). See **`references/template-guide.md`** § "Minimum Content Volume Per Slide Type".
- Active voice, one key message per slide, no jargon. Words to avoid: cheap, fast food, takeaway/takeout, hungry/starving, lazy, naughty, guilty, greedy, diet, swearing.

---

## Visual Identity Rules

Full colour palette, typography specs, line spacing rules, and market-specific colour avoidance in **`references/visual-identity.md`**.

**Essential rules:**
- **JET Orange (`#ff8000`)** must appear in every deck — use orange divider slides (slide 14) between sections.
- **Charcoal (`#242e30`)** for all text on light backgrounds. White text on JET Orange or Aubergine backgrounds.
- **Inter** font family for everything. Divider headlines: Inter Black 36pt. Body: Inter Normal 11pt. Footer: 8pt.
- **Never set text in supporting colours** (Berry, Cupcake, Turmeric, Latte). These are for background blocks only.
- Market restrictions: avoid Turmeric in Bulgaria/Spain/Italy/Israel; avoid Cupcake in Slovakia/Israel/Germany/Denmark.

---

## CLI Command Reference

All commands return structured JSON: `{ok: true, cmd, result}` or `{ok: false, cmd, error, code}`. For the full command listing with all flags and options, see **`references/cli-reference.md`**.

---

## Known Limitations

See **`references/slides-api-gotchas.md`** § "Known Limitations" and **`references/template-guide.md`** for slide-specific quirks.

**Top 3 to remember:** (1) `set-text` strips all formatting — always restore. (2) Group elements need `replaceAllText` via batch, not `set-text`. (3) Cover/closing background images are baked in and cannot be swapped.

---

## Template Images & Content Volume

Many slides have baked-in stock images. If the image is off-topic and no replacement URL is available, choose a different slide variant. See **`references/template-guide.md`** § "Template Image Guide".

Empty space is the #1 visual problem. If you don't have enough content to fill a slide, choose a smaller variant. See **`references/template-guide.md`** § "Minimum Content Volume Per Slide Type".

---

## Post-Population Polish: Vertical Centering

After populating content and restoring formatting, apply `contentAlignment: MIDDLE` via `updateShapeProperties` to short-text elements in tall containers. This eliminates top-heavy dead space.

**Good candidates:** quote bubbles, stat numbers, timeline labels, journey circles, callout boxes, card number labels, severity badges.

**Never center:** body text paragraphs, page titles, footers, bullet lists, or any element in a parallel/grid layout with variable content length (use TOP alignment instead).

For the JSON recipe, per-slide-type guide, and overlap warnings, see **`references/slides-api-gotchas.md`** § "Vertical Centering" and **`references/template-guide.md`** § "Vertical Centering Guide by Slide Type".

---

## Troubleshooting

See **`references/slides-api-gotchas.md`** § "Troubleshooting" for auth issues, text replacement problems, group element handling, overflow fixes, and long JSON workarounds.

**Auth expired:** `scripts/slides-cli auth login --credentials conf/client_secret_602299916251-7aodem5aquraoo8m9goeepn3ugi5ok22.apps.googleusercontent.com.json`
