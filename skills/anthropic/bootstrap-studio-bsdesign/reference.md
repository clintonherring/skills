# Reference: bsdesign Utilities

## CSS-to-Blocks Parser

Converts raw CSS text into Bootstrap Studio's structured block format.

```python
import re

def strip_comments(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)

def strip_imports(css):
    """Remove @import rules (handle separately via headSettings)."""
    return re.sub(r'@import\s+url\([^)]*\)\s*;', '', css)

def parse_declarations(block_body):
    """Split CSS declarations by semicolons, respecting parentheses depth."""
    declarations = []
    depth = 0
    current = []
    for char in block_body:
        if char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth -= 1
            current.append(char)
        elif char == ';' and depth == 0:
            decl = ''.join(current).strip()
            if decl:
                declarations.append(decl)
            current = []
        else:
            current.append(char)
    leftover = ''.join(current).strip()
    if leftover:
        declarations.append(leftover)
    return declarations

def split_selectors(selector_group):
    """Split grouped selectors by comma, preserving brackets/parens/quotes."""
    parts = []
    depth = 0
    current = []
    for char in selector_group:
        if char in '([':
            depth += 1
            current.append(char)
        elif char in ')]':
            depth -= 1
            current.append(char)
        elif char in ('"', "'"):
            current.append(char)
        elif char == ',' and depth == 0:
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)
    leftover = ''.join(current)
    if leftover.strip():
        parts.append(leftover)
    return parts if len(parts) > 1 else [selector_group]

def css_to_blocks(css_text):
    """Parse CSS into Bootstrap Studio block format."""
    css_text = strip_comments(css_text)
    css_text = strip_imports(css_text)
    blocks = []
    pos = 0
    length = len(css_text)

    while pos < length:
        while pos < length and css_text[pos] in ' \t\n\r':
            pos += 1
        if pos >= length:
            break

        brace_pos = css_text.find('{', pos)
        if brace_pos == -1:
            break

        selector = css_text[pos:brace_pos].strip()
        if not selector:
            pos = brace_pos + 1
            continue

        depth = 1
        end_pos = brace_pos + 1
        while end_pos < length and depth > 0:
            if css_text[end_pos] == '{':
                depth += 1
            elif css_text[end_pos] == '}':
                depth -= 1
            end_pos += 1

        body = css_text[brace_pos + 1:end_pos - 1].strip()
        pos = end_pos

        if '{' in body:
            inner = css_to_blocks(body)
            for ib in inner:
                ib['selector'] = selector + ' ' + ib['selector']
                blocks.append(ib)
            continue

        raw_decls = parse_declarations(body)
        rules = []
        for decl in raw_decls:
            colon_pos = decl.find(':')
            if colon_pos == -1:
                continue
            prop = decl[:colon_pos].strip()
            val = decl[colon_pos + 1:].strip()
            if not prop:
                continue
            rules.append({
                "property": prop,
                "value": val,
                "enabled": True,
                "system": False
            })

        selectors = split_selectors(selector)
        for sel in selectors:
            sel = sel.strip()
            if not sel:
                continue
            blocks.append({
                "selector": sel,
                "mediaQuery": False,
                "containerQuery": False,
                "system": False,
                "enabled": True,
                "rules": list(rules)
            })

    return blocks
```

## Injecting a CSS File into a bsdesign

```python
import gzip, json

def inject_css(input_path, output_path, css_name, css_text, priority=1, font_link=None):
    """Inject parsed CSS blocks into a bsdesign file."""
    with gzip.open(input_path, 'rb') as f:
        data = json.loads(f.read())

    blocks = css_to_blocks(css_text)
    design = data['design']

    new_asset = {
        "name": css_name,
        "properties": {},
        "priority": priority,
        "pageBlacklist": [],
        "pageWhitelist": [],
        "blocks": blocks
    }

    children = design['assets']['css']['children']
    children = [c for c in children if c.get('name') != css_name]
    children.insert(0, new_asset)
    design['assets']['css']['children'] = children

    if font_link:
        head = design['settings'].get('headSettings', {})
        existing = head.get('/', '')
        if font_link not in existing:
            head['/'] = font_link + '\n' + existing if existing else font_link
            design['settings']['headSettings'] = head

    data['design'] = design
    with gzip.open(output_path, 'wb', compresslevel=6) as f:
        f.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    return len(blocks)
```

## Page and Component Builders

Helper functions for constructing the HTML component tree.

### Base Node Factory

```python
def make_node(class_name, bootstrap_classes="", properties=None, overrides=None,
              children=None, can_be_edited=False):
    """Create a component node.

    can_be_edited: Only true for text-holding nodes (Heading, Paragraph,
    Button, NavBarBrand, Anchor). Container-type nodes must be false.
    """
    node = {
        "class": class_name,
        "cssClasses": {
            "system": {"main": bootstrap_classes, "customPropClasses": ""},
            "parent": ""
        },
        "overrides": overrides or {},
        "flags": {
            "canBeMoved": True, "canBeDeleted": True, "canBeDuplicated": True,
            "canBeEdited": can_be_edited, "canBePackaged": True, "canBeCopied": True
        },
        "properties": properties or {},
        "customProperties": [],
        "masked": False,
        "unlinkedArea": False,
        "label": "",
        "comment": None,
    }
    if children is not None:
        node["children"] = children
    return node
```

### Text Helpers

```python
def make_inline_char():
    """Create the InlineCharacter node required before text strings."""
    return {
        "class": "InlineCharacter",
        "char": "", "weight": "", "style": "",
        "strike": False, "underline": False, "link": False,
        "target": "", "title": "", "rel": "", "ariaLabel": "",
        "color": "", "bgColor": "", "sub": False, "sup": False
    }

def make_text(text):
    """Wrap text with InlineCharacter prefix (required by BSS)."""
    return [make_inline_char(), text]
```

### Common Component Factories

```python
def make_container(fluid=False, children=None):
    cls = "container-fluid" if fluid else "container"
    return make_node("Container", cls,
        properties={"fluid": fluid, "breakpoint": "", "contextual-color": ""},
        children=children or [])

def make_row(extra_classes="", children=None):
    cls = "row" + (" " + extra_classes if extra_classes else "")
    return make_node("Row", cls,
        properties={"gutters": True, "row-cols": "", "contextual-color": ""},
        children=children or [])

def make_column(sizes=None, children=None):
    """sizes: dict like {"lg": "10", "xl": "8"}"""
    sizes = sizes or {}
    classes = " ".join(f"col-{bp}-{sz}" for bp, sz in sizes.items()) or "col"
    props = {}
    for bp in ("xs", "sm", "md", "lg", "xl", "xxl"):
        props[f"col{bp}"] = sizes.get(bp, -1)
        props[f"col{bp}Offset"] = -1
    props["contextual-color"] = ""
    return make_node("Column", " " + classes, properties=props, children=children or [])

def make_heading(level, text):
    return make_node("Heading", "",
        properties={"type": f"h{level}", "heading-display": "", "contextual-color": ""},
        can_be_edited=True,
        children=make_text(text))

def make_paragraph(text, lead=False):
    return make_node("Paragraph", "",
        properties={"text-lead": lead, "contextual-color": ""},
        can_be_edited=True,
        children=make_text(text))

def make_button(text, href="#", style="btn-primary", outlined=False, size=""):
    bs_class = "btn " + ("btn-outline-" + style.replace("btn-", "") if outlined else style)
    return make_node("Button", bs_class,
        properties={"type": "Link", "style": style, "size": size,
                     "active": False, "outlined": outlined, "disabled": False},
        overrides={"/": {"href": href}},
        can_be_edited=True,
        children=make_text(text))

def make_section(children=None, custom_class=""):
    overrides = {}
    if custom_class:
        overrides = {"/": {"class": custom_class}}
    return make_node("Section", "",
        properties={"contextual-color": ""},
        overrides=overrides,
        children=children or [])

def make_div(children=None, custom_class=""):
    overrides = {}
    if custom_class:
        overrides = {"/": {"class": custom_class}}
    return make_node("Div", "",
        properties={"contextual-color": ""},
        overrides=overrides,
        children=children or [])

def make_icon(icon_class, icon_set="line-awesome"):
    return make_node("Icon", "",
        properties={"icon": icon_class, "iconSet": icon_set,
                     "iconGroup": "all", "contextual-color": ""},
        children=None)
    # Icon nodes have NO children array

def make_image(src, responsive=True):
    return make_node("Image", "img-fluid" if responsive else "",
        properties={"automaticDimensions": True, "responsive": responsive, "aspectRatio": ""},
        overrides={"/": {"src": src}})

def make_anchor(text, href="#", bootstrap_classes=""):
    return make_node("Anchor", bootstrap_classes,
        overrides={"/": {"href": href}},
        can_be_edited=True,
        children=make_text(text))
```

### Navbar Builder (Correct Structure)

```python
def make_navbar(brand_text, brand_href="index.html", nav_items=None):
    """Build a complete navbar.

    nav_items: list of (text, href) tuples.

    Uses correct BSS classes: Anchor (not NavLink), Nav (not NavBarNav).
    """
    brand = make_node("NavBarBrand", "navbar-brand",
        overrides={"/": {"href": brand_href}},
        can_be_edited=True,
        children=make_text(brand_text))

    icon = make_node("Icon", "",
        properties={"icon": "fa fa-bars", "iconGroup": "all",
                     "iconSet": "fa-4", "contextual-color": ""})
    # Icon has no children key

    toggle = make_node("NavBarToggle", "navbar-toggler",
        properties={"float": "end", "contextual-color": ""},
        overrides={"/": {
            "aria-controls": "navbarResponsive",
            "aria-expanded": "false",
            "aria-label": "Toggle navigation",
            "data-bs-target": "#navbarResponsive"
        }},
        children=[icon])

    items = []
    for text, href in (nav_items or []):
        anchor = make_node("Anchor", "nav-link",
            overrides={"/": {"class": "", "href": href}},
            can_be_edited=True,
            children=make_text(text))
        nav_item = make_node("NavItem", "nav-item",
            properties={"disabled": False, "active": False,
                         "contextual-color": "", "matchHref": True},
            children=[anchor])
        nav_item["flags"]["canBePackaged"] = False
        items.append(nav_item)

    nav = make_node("Nav", "nav nav-tabs",
        properties={"type": "tab", "justified": "",
                     "contextual-color": "", "margin-start": "auto"},
        children=items)

    collapse = make_node("NavBarCollapse", "collapse navbar-collapse",
        properties={"contextual-color": ""},
        overrides={"/": {"id": "navbarResponsive"}},
        children=[nav])

    return make_node("NavBar", "navbar navbar-expand-lg fixed-top",
        properties={"position": "fixed-top", "fluid": False,
                     "expanded": "navbar-expand-lg",
                     "smartActiveState": False, "contextual-color": ""},
        children=[brand, toggle, collapse])
```

### Deep-Copy from Existing Page (Recommended)

The safest way to add navbars/footers to new pages is to deep-copy from an existing page. This avoids any risk of using wrong class names, missing fields, or incorrect flags.

```python
import copy

def extract_templates(design, source_page_name='index.html'):
    """Extract navbar and footer from an existing page.

    Returns (navbar_template, footer_template) as deep copies.
    """
    source = None
    for p in design['pages']['children']:
        if not isinstance(p, dict): continue
        if p.get('name') == source_page_name and 'html' in p:
            source = p
            break
        if 'children' in p:
            for sub in p.get('children', []):
                if isinstance(sub, dict) and sub.get('name') == source_page_name and 'html' in sub:
                    source = sub
                    break

    if not source:
        raise ValueError(f"Page {source_page_name} not found")

    body = source['html']['children'][0]
    navbar = None
    footer = None
    for child in body.get('children', []):
        if isinstance(child, dict):
            if child.get('class') == 'NavBar' and not navbar:
                navbar = copy.deepcopy(child)
            if child.get('class') == 'Footer':
                footer = copy.deepcopy(child)

    return navbar, footer


def apply_templates_to_page(page, navbar, footer, content_children):
    """Replace a page's body with navbar + content + footer."""
    body = page['html']['children'][0]
    body['children'] = [
        copy.deepcopy(navbar),
        *content_children,
        copy.deepcopy(footer)
    ]
```

### Validation

```python
VALID_CLASSES = {
    'HTML', 'Body', 'NavBar', 'NavBarBrand', 'NavBarToggle', 'NavBarCollapse',
    'Nav', 'NavItem', 'Anchor', 'Icon', 'Header', 'Footer', 'Section',
    'Container', 'Row', 'Column', 'Heading', 'Paragraph', 'Button', 'Image',
    'Div', 'Span', 'List', 'ListItem', 'Hr', 'DefaultCard', 'CardBody',
    'Form', 'InputEmail', 'InputText', 'InputTextarea', 'InlineCharacter'
}

def validate_classes(node, invalid=None):
    """Walk a component tree and collect any invalid class names."""
    if invalid is None:
        invalid = set()
    if not isinstance(node, dict):
        return invalid
    cls = node.get('class', '')
    if cls and cls not in VALID_CLASSES:
        invalid.add(cls)
    for child in node.get('children', []):
        validate_classes(child, invalid)
    return invalid

def validate_file(bsdesign_path):
    """Validate all component classes in a bsdesign file."""
    import gzip, json
    with gzip.open(bsdesign_path, 'rb') as f:
        data = json.loads(f.read())

    invalid = set()
    for p in data['design']['pages']['children']:
        if not isinstance(p, dict): continue
        if 'html' in p:
            validate_classes(p['html'], invalid)
        if 'children' in p:
            for sub in p.get('children', []):
                if isinstance(sub, dict) and 'html' in sub:
                    validate_classes(sub['html'], invalid)

    return invalid
```

### Building a Complete Page

```python
import time

def make_page(name, title, body_children, meta_description=""):
    body = make_node("Body", "",
        properties={"contextual-color": ""},
        children=body_children)

    html_root = {
        "class": "HTML",
        "cssClasses": {"system": {"customPropClasses": ""}, "parent": ""},
        "overrides": {"/": {}},
        "flags": {"canBeMoved": False, "canBeDeleted": False, "canBeDuplicated": False,
                  "canBeEdited": False, "canBePackaged": False, "canBeCopied": False},
        "properties": {"contextual-color": ""},
        "customProperties": [],
        "masked": False,
        "unlinkedArea": False,
        "label": "",
        "comment": "",
        "children": [body]
    }

    meta = []
    if meta_description:
        meta.append({"type": "name", "key": "description", "content": meta_description})

    return {
        "name": name,
        "properties": {},
        "priority": 0,
        "pageBlacklist": [],
        "pageWhitelist": [],
        "html": html_root,
        "meta": meta,
        "includeInExport": True
    }
```

### Adding an Image Asset

```python
import base64, os

def add_image_asset(design, file_path):
    """Read an image file and add it to design assets."""
    name = os.path.basename(file_path)
    ext = os.path.splitext(name)[1].lstrip('.')
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "svg": "image/svg+xml", "gif": "image/gif", "webp": "image/webp"}
    mime = mime_map.get(ext, f"image/{ext}")

    with open(file_path, 'rb') as f:
        raw = f.read()

    b64 = base64.b64encode(raw).decode('ascii')
    data_uri = f"data:{mime};base64,{b64}"

    asset = {
        "name": name,
        "properties": {},
        "priority": 0,
        "pageBlacklist": [],
        "pageWhitelist": [],
        "extension": ext,
        "data": data_uri,
        "fileSize": len(raw),
        "timestamp": int(time.time() * 1000),
        "dimensions": {"x": 0, "y": 0}
    }
    design['assets']['images']['children'].append(asset)
    return name
```

### CSS Block Helpers

```python
def make_rule(prop, value):
    return {"property": prop, "value": value, "enabled": True, "system": False}

def make_block(selector, declarations):
    """Create a CSS block from a selector and {property: value} dict."""
    return {
        "selector": selector,
        "mediaQuery": False,
        "containerQuery": False,
        "system": False,
        "enabled": True,
        "rules": [make_rule(p, v) for p, v in declarations.items()]
    }
```
