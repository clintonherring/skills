---
name: bootstrap-studio-bsdesign
description: Read, edit, and build Bootstrap Studio .bsdesign project files programmatically. Use when the user mentions .bsdesign files, Bootstrap Studio projects, injecting CSS themes into Bootstrap Studio, modifying Bootstrap Studio pages, extracting assets from bsdesign files, or building bsdesign projects from scratch.
---

# Bootstrap Studio .bsdesign File Format

## File Format

A `.bsdesign` file is **gzip-compressed JSON**. Read/write with Python:

```python
import gzip, json

# Read
with gzip.open('project.bsdesign', 'rb') as f:
    data = json.loads(f.read())

# Write (preserves original -- always write to a NEW file)
with gzip.open('project-modified.bsdesign', 'wb', compresslevel=6) as f:
    f.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
```

Magic bytes: `1F 8B` (standard gzip).

## Top-Level Structure

```json
{
  "version": 86,
  "timestamp": 1773327271183,
  "design": { ... }
}
```

## Design Object

```
design
├── id                    # Unique project ID
├── name                  # Project display name
├── framework             # "5" for Bootstrap 5
├── settings              # Project-wide settings (see below)
├── placeholders          # Brand name, description
├── assets
│   ├── images            # { name, children: [...] }
│   ├── fonts             # { name, children: [...] }
│   ├── css               # { name, children: [...] }
│   └── js                # { name, children: [...] }
├── pages                 # { name, expanded, children: [...] }
├── collections           # Blog posts, tags, authors
├── colorMode             # "light" or "dark"
├── colorModeOverrides    # { "light": {}, "dark": {} }
├── reflow                # Reflow CMS settings
├── reflowLocale
└── reflowTestMode
```

## Settings

```json
{
  "theme": { "id": "new-age", "type": "template" },
  "lang": "en",
  "title": "Project Name",
  "websiteURL": "https://example.com",
  "iconSet": "line-awesome",
  "headSettings": { "/": "<link ...>" },
  "meta": [{ "type": "name", "key": "description", "content": "..." }],
  "favicons": [{ "id": "16x16", "src": "icon.png", "type": "image/png", "theme": "", "dimensions": {"width":32,"height":32} }],
  "pwa": { "enabled": false },
  "sitemap": { "enabled": true },
  "canonicalLinks": { "enabled": true },
  "jqueryVersion": "",
  "viewportContent": "",
  "adsTxtContent": "",
  "robotsTxtContent": ""
}
```

The `headSettings` object maps page paths to raw HTML injected into `<head>`. Key `"/"` applies to all pages.

## CSS Assets

CSS is stored as structured blocks, NOT raw text.

```json
{
  "name": "styles.css",
  "properties": {},
  "priority": 0,
  "pageBlacklist": [],
  "pageWhitelist": [],
  "blocks": [
    {
      "selector": ".card",
      "mediaQuery": false,
      "containerQuery": false,
      "system": false,
      "enabled": true,
      "rules": [
        { "property": "border-radius", "value": "0.75rem", "enabled": true, "system": false }
      ]
    }
  ]
}
```

Key details:
- `priority`: Higher number = loads later (higher specificity position)
- `pageBlacklist`/`pageWhitelist`: Limit CSS to specific pages
- `selector`: Any valid CSS selector (`:root`, `[data-bs-theme="dark"]`, `.btn-primary`, etc.)
- CSS custom properties (`--var-name`) go as `property` with value as `value`
- `!important` is part of the value string: `"value": "#fff !important"`
- Grouped selectors (`.a, .b { }`) should be split into separate blocks

### Parsing CSS into Blocks

For a complete CSS-to-blocks parser, see [reference.md](reference.md). Key approach:

1. Strip comments and `@import` statements
2. Find selector + `{...}` pairs (handle nested braces)
3. Split declarations by `;` (respect parens depth)
4. Split grouped selectors by `,` (respect brackets/quotes)
5. `@import` rules go into `headSettings` as `<link>` tags instead

## JS Assets

JS uses a `value` field with raw source code:

```json
{
  "name": "script.js",
  "properties": {},
  "priority": 0,
  "pageBlacklist": [],
  "pageWhitelist": [],
  "value": "console.log('hello');",
  "disabled": false
}
```

## Image Assets

Images are base64-encoded data URIs:

```json
{
  "name": "logo.png",
  "properties": {},
  "priority": 0,
  "pageBlacklist": [],
  "pageWhitelist": [],
  "extension": "png",
  "data": "data:image/png;base64,iVBOR...",
  "fileSize": 12353,
  "timestamp": 1530520541195,
  "dimensions": { "x": 135, "y": 40 }
}
```

## Pages

Pages live in `design.pages.children[]`. Each page:

```json
{
  "name": "index.html",
  "properties": {},
  "priority": 0,
  "pageBlacklist": [],
  "pageWhitelist": [],
  "html": { ... },
  "meta": [{ "type": "name", "key": "description", "content": "Page desc" }],
  "includeInExport": true
}
```

Folders are objects with `name`, `expanded`, `children`, `includeInExport`.

## HTML Component Tree

The `html` field is a recursive tree. Every node has this shape:

```json
{
  "class": "ComponentType",
  "cssClasses": {
    "system": { "main": "bootstrap-classes", "customPropClasses": "" },
    "parent": ""
  },
  "overrides": { "/": { "id": "myId", "href": "#" } },
  "flags": {
    "canBeMoved": true, "canBeDeleted": true, "canBeDuplicated": true,
    "canBeEdited": true, "canBePackaged": true, "canBeCopied": true
  },
  "properties": { ... },
  "customProperties": [],
  "masked": false,
  "unlinkedArea": false,
  "label": "",
  "comment": null,
  "children": [ ... ]
}
```

### Valid Component Classes (Exhaustive)

CRITICAL: Only these class names are valid. Using anything else will corrupt the file and Bootstrap Studio will refuse to open it.

| class | Bootstrap output | canBeEdited | Key properties |
|-------|-----------------|-------------|----------------|
| `HTML` | `<html>` | false | Root node, exactly 1 child (Body). flags: all false |
| `Body` | `<body>` | false | `contextual-color` |
| `NavBar` | `<nav class="navbar">` | **false** | `position`, `fluid`, `expanded`, `smartActiveState`, `contextual-color` |
| `NavBarBrand` | `<a class="navbar-brand">` | true | (none) |
| `NavBarToggle` | `<button class="navbar-toggler">` | **false** | `float`, `contextual-color` |
| `NavBarCollapse` | `<div class="collapse navbar-collapse">` | **false** | `contextual-color` |
| `Nav` | `<ul class="nav nav-tabs">` | **false** | `type` ("tab"), `justified`, `margin-start`, `contextual-color` |
| `NavItem` | `<li class="nav-item">` | **false** | `disabled`, `active`, `matchHref`, `contextual-color`. flags: canBePackaged=false |
| `Anchor` | `<a>` | true | Used for nav links (`nav-link` bootstrap class), generic links. `href` in overrides |
| `Header` | `<header>` | false | `contextual-color` |
| `Section` | `<section>` | false | `text-alignment`, `contextual-background`, `contextual-color` |
| `Footer` | `<footer>` | false | `contextual-color` |
| `Container` | `<div class="container">` | false | `fluid`, `breakpoint`, `contextual-color` |
| `Row` | `<div class="row">` | false | `gutters`, `row-cols`, `row-cols-{bp}`, `contextual-color` |
| `Column` | `<div class="col-*">` | false | `colxs`..`colxxl`, offset variants (`colxsOffset`..`colxxlOffset`), `contextual-color` |
| `Heading` | `<h1>`..`<h6>` | true | `type` ("h1".."h6"), `heading-display`, `contextual-color` |
| `Paragraph` | `<p>` | true | `text-lead`, `contextual-color` |
| `Button` | `<a class="btn">` or `<button>` | true | `type` ("Link"/"Submit"), `style`, `size`, `outlined`, `active`, `disabled` |
| `Image` | `<img>` | false | `responsive`, `src` (in overrides) |
| `Icon` | `<i class="icon-class">` | **false** | `icon`, `iconSet`, `iconGroup`, `contextual-color` |
| `Div` | `<div>` | false | Generic container. `contextual-color` |
| `Span` | `<span>` | false | Inline container |
| `Anchor` | `<a>` | true | Generic anchor. `href` in overrides |
| `List` | `<ul>` | false | `style` ("inline", "unstyled", etc.) |
| `ListItem` | `<li>` | false | |
| `Hr` | `<hr>` | false | |
| `DefaultCard` | `<div class="card">` | false | |
| `CardBody` | `<div class="card-body">` | false | |
| `Form` | `<form>` | false | |
| `InputEmail` | `<input type="email">` | false | |
| `InputText` | `<input type="text">` | false | |
| `InputTextarea` | `<textarea>` | false | |

**INVALID class names** (these will break the file):
- ~~`NavLink`~~ → Use `Anchor` with `cssClasses.system.main = "nav-link"`
- ~~`NavBarNav`~~ → Use `Nav` with `cssClasses.system.main = "nav nav-tabs"`
- ~~`Card`~~ → Use `DefaultCard`

### Text Content

Text appears as plain strings or `InlineCharacter` objects in `children`:

```json
{
  "class": "InlineCharacter",
  "char": "",
  "weight": "",
  "style": "",
  "strike": false,
  "underline": false,
  "link": false,
  "target": "",
  "title": "",
  "rel": "",
  "ariaLabel": "",
  "color": "",
  "bgColor": "",
  "sub": false,
  "sup": false
}
```

A heading with text: `"children": [{ "class": "InlineCharacter", ... }, "Hello World"]`

### Overrides

The `overrides` dict maps page paths to HTML attribute overrides:
- `"/"` = all pages
- `"/about.html"` = specific page only

Common override keys: `id`, `href`, `src`, `class` (adds extra CSS classes to the element), `data-*`, `aria-*`, `style`.

### Adding Custom CSS Classes to Elements

Use the `overrides` field with key `"class"` to add CSS classes beyond the system ones:

```json
{
  "class": "Div",
  "cssClasses": { "system": { "customPropClasses": "" }, "parent": "" },
  "overrides": { "/": { "class": "osar-legal-card my-custom-class" } }
}
```

The `cssClasses.system.main` contains the Bootstrap framework classes. The `overrides["/"]["class"]` adds additional custom classes.

## Navbar Structure (Correct)

The navbar must follow this exact hierarchy:

```
NavBar (navbar navbar-expand-lg fixed-top)
├── NavBarBrand (navbar-brand)
│   ├── InlineCharacter
│   └── "Brand Text"
├── NavBarToggle (navbar-toggler)
│   └── Icon (fa fa-bars)
└── NavBarCollapse (collapse navbar-collapse)  [id: navbarResponsive]
    └── Nav (nav nav-tabs)  [properties: type="tab", margin-start="auto"]
        ├── NavItem (nav-item)  [properties: disabled=false, active=false, matchHref=true]
        │   └── Anchor (nav-link)  [overrides: href="#section"]
        │       ├── InlineCharacter
        │       └── "Link Text"
        └── NavItem ...
```

Key facts:
- `Nav` uses type `"tab"` and `cssClasses.system.main = "nav nav-tabs"` (even for navbar nav)
- `NavItem` has `canBePackaged: false` in flags
- Nav links use `Anchor` class (not `NavLink` which doesn't exist)
- `NavBarToggle` must have `data-bs-target: "#navbarResponsive"` matching the collapse `id`

## Best Practices for Page Restructuring

### Deep-Copy Pattern (Recommended)

When adding navbars, footers, or other complex components to new/bland pages, **deep-copy them from an existing page** rather than building from scratch. This guarantees all required fields, flags, and properties are correct:

```python
import copy

# Extract templates from a known-good page
index_page = find_page(design, 'index.html')
index_body = index_page['html']['children'][0]

navbar_template = None
footer_template = None
for child in index_body.get('children', []):
    if isinstance(child, dict):
        if child.get('class') == 'NavBar':
            navbar_template = child
        if child.get('class') == 'Footer':
            footer_template = child

# Use deep copies on other pages
new_body_children = [
    copy.deepcopy(navbar_template),
    # ... your page content ...
    copy.deepcopy(footer_template)
]
```

### Validation After Modification

Always verify that every component node uses a valid class name:

```python
VALID_CLASSES = {
    'HTML', 'Body', 'NavBar', 'NavBarBrand', 'NavBarToggle', 'NavBarCollapse',
    'Nav', 'NavItem', 'Anchor', 'Icon', 'Header', 'Footer', 'Section',
    'Container', 'Row', 'Column', 'Heading', 'Paragraph', 'Button', 'Image',
    'Div', 'Span', 'List', 'ListItem', 'Hr', 'DefaultCard', 'CardBody',
    'Form', 'InputEmail', 'InputText', 'InputTextarea', 'InlineCharacter'
}

def validate_classes(node, invalid=None):
    if invalid is None: invalid = set()
    if not isinstance(node, dict): return invalid
    cls = node.get('class', '')
    if cls and cls not in VALID_CLASSES:
        invalid.add(cls)
    for child in node.get('children', []):
        validate_classes(child, invalid)
    return invalid
```

## Building a Project from Scratch

Minimal valid `.bsdesign`:

```python
import gzip, json, time, base64

project = {
    "version": 86,
    "timestamp": int(time.time() * 1000),
    "design": {
        "id": f"project_{int(time.time() * 1000)}",
        "name": "My Project",
        "framework": "5",
        "settings": {
            "theme": {"id": "default", "type": "template"},
            "lang": "en",
            "title": "My Project",
            "websiteURL": "",
            "iconSet": "line-awesome",
            "headSettings": {},
            "meta": [],
            "favicons": [],
            "pwa": {"enabled": False},
            "sitemap": {"enabled": True},
            "canonicalLinks": {"enabled": True},
            "jqueryVersion": "",
            "viewportContent": "",
            "adsTxtContent": "",
            "robotsTxtContent": "",
            "appAdsTxtContent": "",
            "ecommerce": {"store": None}
        },
        "placeholders": {"brand": "My Brand", "description": "Description"},
        "assets": {
            "images": {"name": "", "expanded": True, "children": []},
            "fonts": {"name": "", "expanded": True, "children": []},
            "css": {"name": "", "expanded": True, "children": []},
            "js": {"name": "", "expanded": True, "children": []}
        },
        "pages": {
            "name": "",
            "expanded": True,
            "children": []
        },
        "collections": [],
        "colorMode": "light",
        "colorModeOverrides": {"light": {}, "dark": {}},
        "reflow": None,
        "reflowLocale": None,
        "reflowTestMode": False
    }
}

# Add a page -- see reference.md for helper functions
# ...

with gzip.open('new-project.bsdesign', 'wb', compresslevel=6) as f:
    f.write(json.dumps(project, ensure_ascii=False).encode('utf-8'))
```

## Safety Rules

- **Never modify the original file** -- always write to a new path
- **Verify after writing** -- decompress and check JSON validity
- **Validate component classes** -- run the validator above on all page trees
- **Preserve all existing data** -- only add/modify specific fields
- **Deep-copy complex components** -- never hand-build navbars/footers from scratch
- Images can be very large (base64) -- be mindful of memory when loading

## Common Pitfalls

1. **Invalid class names**: BSS silently fails with "Something went wrong" if any node uses a class name it doesn't recognize. Always validate.
2. **Wrong `canBeEdited` flag**: Container-type components (NavBar, Nav, NavBarCollapse, NavBarToggle, Container, Row, Column, Div, Section, Footer, Icon) must have `canBeEdited: false`. Only text-holding components (Heading, Paragraph, Button, NavBarBrand, Anchor) should be `true`.
3. **Missing `InlineCharacter`**: Text content in editable nodes must be preceded by an `InlineCharacter` object. Pattern: `"children": [InlineCharacter, "text string"]`.
4. **NavItem flags**: `NavItem` must have `canBePackaged: false` (unlike most other nodes).
5. **Nav type**: Even inside a navbar, `Nav` uses `type: "tab"` and bootstrap class `"nav nav-tabs"`.
6. **Inline style conflicts**: If a BSS template has inline `style` overrides (e.g., background gradients), they override CSS assets. Clear them by setting `overrides["/"]["style"] = ""`.

## Additional Resources

- For CSS parsing utilities and page-building helpers, see [reference.md](reference.md)
