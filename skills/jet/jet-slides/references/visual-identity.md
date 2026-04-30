# JET Visual Identity Reference for Presentations

> Source: Brand Refresh Style Guide 2024 (Presentation `1leICK7p9YsbpTJAxuRMm15J46euV_pjYhOD_o1G6lqI`)
> Focus: rules relevant to Google Slides presentation creation

## Core Principle

"Creative that can flex" — visual communications are always unmistakably JET, but the design system flexes by market, audience, vertical, and asset.

## Colour Palette

### Primary
| Colour | Hex | Usage |
|--------|-----|-------|
| **JET Orange** | `#ff8000` | Primary brand colour — MUST appear in every communication |
| **Accessible Orange** | `#f36805` | Interactive buttons and icons only (accessibility) |

### Supporting Colours
| Colour | Hex | Usage |
|--------|-----|-------|
| **Berry** | `#f2a6b0` | Colour blocks and backgrounds |
| **Cupcake** | `#c1dade` | Colour blocks and backgrounds |
| **Turmeric** | `#f6c243` | Colour blocks and backgrounds |
| **Latte** | `#e7cda2` | Colour blocks and backgrounds (replaced Tomato) |
| **Aubergine** | `#5b3d5b` | Highlights only in certain product placements; NEVER as solid background blocks |

### Neutrals
| Colour | Hex | Usage |
|--------|-----|-------|
| **Charcoal** | `#242e30` | Text and interactive elements ONLY — never as solid background |
| **Mozzarella** | `#efedea` | Background colour |
| **Mozzarella Tint 1** | `#f5f3f1` | Background colour |
| **Mozzarella Tint 2** | `#fcfcfc` | Background colour |

### Extended Light Palette
| Colour | Hex |
|--------|-----|
| Berry Light | `#f9d2d7` |
| Cupcake Light | `#e0ecee` |
| Turmeric Light | `#fae0a1` |
| Latte Light | `#f1e3c9` |
| Orange Light | `#fddfc3` |

## Colour Rules

### Critical Don'ts
1. **Never use more than one supporting colour per layout** — use one supporting colour with JET Orange
2. **Never use Charcoal as a solid background** — reserve for text only
3. **Never use blocks of Aubergine** — use sparingly as accent only
4. **Never place logo over a supporting colour** — logo goes on JET Orange or white
5. **Never use Charcoal for the logo** — always JET Orange or White
6. Tomato is no longer used — Latte has replaced it

### Type Colour Rules (for slide text)
| Background | Text Colour |
|-----------|------------|
| White / Mozzarella / Mozzarella Tints | Charcoal or JET Orange |
| Berry | Charcoal |
| Turmeric | Charcoal |
| Cupcake | Charcoal |
| Latte | Charcoal |
| JET Orange | White |
| Aubergine | White |

**Never set type in supporting colours.**

### Market-Specific Colour Avoidance
| Colour to Avoid | Markets |
|-----------------|---------|
| Turmeric | Bulgaria, Spain, Italy, Israel |
| Cupcake | Slovakia, Israel, Germany, Denmark |

### Orange Usage Principle
The amount of JET Orange depends on audience familiarity with the brand:
- **More orange** → loyal/active customers, well-established markets
- **Less orange** → awareness campaigns, new markets
- Minimum 20% of slides/frames should use JET Orange as background

## The Bookend Principle

For sequential content like presentations:
1. **Start on JET Orange** (first slide)
2. **Introduce supporting colours** in the middle sections
3. **End on JET Orange** (last slide)
4. Supporting colours should be used in **sections** (not one different colour per slide)
5. Minimum **20% of slides** should have JET Orange background
6. Shorter sequences can use single frames of supporting colours

## Typography for Presentations

### Font: Inter (NOT JET Sans)
JET Sans is for consumer-facing materials. **Presentations use Inter.**

### Type Hierarchy for Slides
| Role | Font | Size |
|------|------|------|
| Divider headlines | Inter Black | 36pt |
| Cover headlines (line 1) | Inter Black (900) | 36pt |
| Cover subtitles (line 2) | Inter Medium (500) | 18pt |
| Long text headlines | Inter Bold | 19pt |
| Subtitles | Inter Bold | 11pt |
| Card headings | Inter Extra Bold (800) | 13pt |
| Body text | Inter Normal | 11pt |
| Footer | Inter Normal/Bold | 8pt |
| Sources | Inter Normal | 7pt |

### Line Spacing
- **1.15** line spacing for body text

### Alignment
- **Left aligned** by default for formal/corporate presentations
- Sentence case for all text in presentations (formal/corporate context)

### Type Weight Rules
- Don't mix font weights in one piece of copy
- Don't use Extra Black for body copy
- Don't mix Extra Black and Extra Black Italic
- Don't set text in supporting colours
- Don't set text too tightly or too loosely spaced

### Underline Rule (CRITICAL)
- **Never underline text** unless it is a clickable hyperlink
- Underlined non-link text is a brand violation
- This applies to all slide text: headings, body, cards, labels, quotes, attributions
- When the API or template introduces underlines accidentally (e.g., via `set-text` formatting loss), explicitly remove them with `updateTextStyle` setting `underline: false` in the style fields

## Grid System

- **12-column layout** for 16:9 presentations
- Margin: 6% of shortest side
- Gutter: 60% of margin width
- Colour blocks sit in ratios of thirds (⅓) or quarters (¼) and align to grid

### Template text box padding
Text boxes in the JET slide template are intentionally smaller than their surrounding background shapes. This gap creates visual padding and margins — it is part of the template design, not a bug. Do not resize text boxes to match background shapes unless text is genuinely overflowing and cannot be shortened. See `slides-api-gotchas.md` for the resize recipe when resizing is truly necessary.

## Vertical Centering

After populating a deck, apply vertical centering (`contentAlignment: MIDDLE`) to **self-contained** short-text elements in tall containers — quote bubbles, stat numbers, journey circles, callout boxes, cover titles, divider headlines, and point page numbers.

**Do NOT center:**
- Body text paragraphs, page titles, footers, bullet lists
- Label headings that sit above separate body text (causes overlap)
- **Elements in parallel/grid layouts with variable content length** — this includes timeline month boxes, 6-card grid bodies, breadcrumb sub-step descriptions, process roadmap descriptions below chevrons, and journey map finding descriptions. In these layouts, MIDDLE centering causes shorter content to float down while longer content stays near the top, breaking horizontal baseline alignment.

**Key distinction:** Number labels, chevron labels, and other single-value elements within parallel layouts can keep MIDDLE. Only the variable-length body/description text must use TOP.

See `slides-api-gotchas.md` and `template-guide.md` for full guidance.

## Imagery Guidelines (for slides with images)

- Food photography is always the star
- Hero product images on supporting colour plinths — match plinth to background colour
- Only one supporting colour per layout
- Match background colours tonally to image colours
- Backgrounds should always be solid
- Tight crops for hero model shots
- Include drips, melts, sizzles for food (implied motion)
- Prioritise visuals over text (Behavioural Science finding)
- Adding people and faces attracts attention
