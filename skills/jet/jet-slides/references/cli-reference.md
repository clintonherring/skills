# slides-cli Command Reference

All commands return structured JSON: `{ok: true, cmd, result}` or `{ok: false, cmd, error, code}`.

## Authentication

```bash
slides-cli auth login --credentials <path>     # Authenticate via Google OAuth2
slides-cli auth status                          # Check auth status
slides-cli auth logout                          # Clear stored token
```

## Presentation Info

```bash
slides-cli presentation info --presentation <id>    # Get metadata (title, slide count, dimensions)
slides-cli presentation find --name <query>          # Search by name in Google Drive
```

## Layouts

```bash
slides-cli layouts --presentation <id>               # List available layouts
```

## Reading Slides

```bash
slides-cli read slide --presentation <id> --index <n>        # Read one slide's elements (incl. group children)
slides-cli read slide --presentation <id> --all              # Read ALL slides at once
slides-cli read text --presentation <id>                     # Extract all text from presentation
```

## Creating Presentations

```bash
slides-cli create from-template --template <id> --title <name> [--folder <id>]
```

## Editing

```bash
slides-cli edit replace-text --presentation <id> --replacements <json>
# Global find-and-replace across all slides. JSON array of {placeholder, value}.

slides-cli edit set-text --presentation <id> --object-id <id> --text <text>
# Set text on a specific element. WARNING: strips all formatting — restore with updateTextStyle.
# Use \n for line breaks — the CLI auto-converts to real newlines.

slides-cli edit delete-slide --presentation <id> --slide-id <id>
# Delete a single slide by objectId.

slides-cli edit delete-slides --presentation <id> --slide-ids <json>
# Delete multiple slides. JSON array of objectIds.

slides-cli edit duplicate-slide --presentation <id> --slide-id <id> [--position <n>]
# Duplicate a slide. Duplicated slide gets new objectIds — use `read slide` to discover them.

slides-cli edit delete-element --presentation <id> --element-id <id>
# Delete a page element (shape, image, group, etc.).

slides-cli edit reorder-slides --presentation <id> --slide-ids <json> --position <n>
# Move slides to a new position. Uses --slide-ids (plural) and --position (not --index).

slides-cli edit insert-image --presentation <id> --object-id <id> --image-url <url>
# Replace an image placeholder with an image from a URL.

slides-cli edit set-speaker-notes --presentation <id> --slide-id <id> --text <text>
# Set speaker notes on a slide.

slides-cli edit batch --presentation <id> --requests <json>
# Send raw Google Slides API requests. For complex operations (updateTextStyle,
# replaceAllText, updatePageElementTransform, updateParagraphStyle, etc.).

slides-cli edit update-element --presentation <id> --object-id <id> [--x <emu>] [--y <emu>] [--width <emu>] [--height <emu>]
# Move or resize a page element. All values in EMU (1 inch = 914400 EMU).

slides-cli edit update-text-style --presentation <id> --object-id <id> [--font <name>] [--size <pt>] [--bold <bool>] [--italic <bool>] [--color <hex>] [--start <n>] [--end <n>]
# Style text on an element. Optional --start/--end for character range styling.
```

## Sharing

```bash
slides-cli share user --presentation <id> --email <email> [--role <role>]
# Share with a specific user. Roles: reader, writer, commenter.

slides-cli share domain --presentation <id> --domain <domain> [--role <role>]
# Share with an entire domain.
```

## Exporting

```bash
slides-cli export thumbnails --presentation <id> --output <dir> [--scale <1-4>]
# Export slide thumbnails as PNGs. Files saved as slide-00.png, slide-01.png, etc.
```

## Moving

```bash
slides-cli move --presentation <id> --folder <id>
# Move presentation to a Google Drive folder.
```

## Tips

- For long JSON arguments, write to a temp file: `--slide-ids "$(cat /tmp/ids.json)"`
- Use `edit batch` to combine multiple operations into fewer API calls (rate limit: ~60 req/min)
- `replaceAllText` works inside group elements; `set-text` does NOT (it prepends instead of replacing)
