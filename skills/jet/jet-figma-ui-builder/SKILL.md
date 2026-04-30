---
name: jet-figma-ui-builder
description: |
  Iteratively builds UI components from a Figma design using PIE web components,
  PIE icons, and PIE design tokens, validating each build step with live Chrome
  DevTools screenshots. Use this skill when asked to implement a Figma design,
  build UI from a Figma URL, create a screen, page, or component from a design
  file, or when phrases like "build this design", "implement this Figma", "Figma
  to code", "pixel-perfect", "match the design", or "implement the UI" appear
  alongside a Figma link. Also use when the user wants to iteratively validate
  UI against a design with live screenshots.
metadata:
  owner: ai-platform
---

# jet-figma-ui-builder

Iteratively implement a Figma design as code, component by component, using PIE
web components and design tokens. After each component is written, take a live
screenshot via Chrome DevTools, show it to the user, and use your own vision to
validate it against the Figma spec — repeating until each component matches
before moving on.

---

## Step 0 — Prerequisites (do this before anything else)

Check all three gates below. If any fail, report **all** failures at once before
stopping — don't make the user fix one and re-run only to discover the next.

### Gate 1 — `pie-design-system` skill

Check whether the file exists at either of these locations:

- `~/.agents/skills/pie-design-system/SKILL.md`
- `.agents/skills/pie-design-system/SKILL.md` (project-local)

If absent:

> **Missing: `pie-design-system` skill**
> This skill requires the PIE design system skill to look up components, tokens,
> and icons correctly. Install it at:
> https://pie.design/agents/resources/#:~:text=Agentic%20AI%20Resources,-This%20page%20provides

### Gate 2 — Figma MCP server

Read `~/.config/opencode/opencode.jsonc` and check that `mcp.figma` exists and
`mcp.figma.enabled` is `true`.

If absent or disabled:

> **Missing: Figma MCP server**
> The Figma MCP server is not configured or is disabled.
> Setup guide: https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server

### Gate 3 — Chrome DevTools MCP server

In the same config file, check that `mcp["chrome-devtools"]` exists and
`mcp["chrome-devtools"].enabled` is `true`.

If absent or disabled:

> **Missing: Chrome DevTools MCP server**
> The Chrome DevTools MCP server is not configured or is disabled.
> Setup guide: https://github.com/ChromeDevTools/chrome-devtools-mcp

---

### Gather session inputs

Once all gates pass, collect the following before proceeding. Ask for anything
not already provided:

| Input              | Notes                                                                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Figma URL**      | Extract `fileKey` from the URL path and `nodeId` from the `node-id` query param if present                                               |
| **Dev server URL** | The dev server is assumed to be already running — ask for the URL if not given (e.g. `http://localhost:5173`)                            |
| **Preview route**  | The URL path Chrome should navigate to (e.g. `/campaigns/new`)                                                                           |
| **Tech stack**     | Glob for `*.vue`, `*.tsx`, `*.jsx`, `package.json`, `tsconfig.json` to detect framework — summarise findings and ask the user to confirm |
| **Max passes**     | How many screenshot/fix rounds to run per component before moving on. Ask the user — default is **5** if they don't specify              |

---

## Step 1 — Ingest the Figma design

1. Call `figma_get_figma_data` with the extracted `fileKey`. Pass `nodeId` if one
   was provided — this scopes the response to just the relevant frame or
   component rather than the entire file.

2. Call `figma_download_figma_images` for any nodes that carry image fills or
   icon assets. Save downloaded files under `src/assets/`.

### Figma rate limits

If either `figma_get_figma_data` or `figma_download_figma_images` returns a rate
limit error (HTTP 429 or a message indicating the limit has been reached), **stop
immediately** and ask the user:

> "The Figma API is rate limited. How would you like to proceed?
>
> 1. **Wait and retry** — I'll pause 60 seconds and try again
> 2. **Use Figma in the browser** — I'll open Figma in Chrome and read the
>    design by navigating the canvas directly via Chrome DevTools
> 3. **Stop** — I'll summarise what was fetched so far so you can resume later"

- If the user says **wait and retry**: pause for 60 seconds, then retry the
  failed call once. If it fails again, offer the same three options again — do
  not silently loop.
- If the user says **use Figma in the browser**: use `chrome-devtools_new_page`
  to open the Figma URL in Chrome, then use `chrome-devtools_take_screenshot`
  and `chrome-devtools_navigate_page` to inspect the design visually. Read
  frame names, colours, spacing, and component structure by screenshotting
  individual frames and using your vision to extract the design intent. This is
  slower and less precise than the MCP data, so note which frames were read
  this way and flag any values you had to approximate.
- If the user says **stop**: summarise what was successfully fetched so far
  (e.g. which frames were retrieved, which images were downloaded) so the
  session can be resumed without repeating work, then halt.

Do not proceed with partial Figma data without the user's explicit go-ahead —
building against an incomplete design spec produces components that will need
rework.

3. Produce a **component inventory** — a structured list you'll work through in
   Step 3. For each frame or component, note:
   - Name and bounding dimensions
   - Colours used (fill, stroke, text)
   - Typography styles (weight, size, line-height)
   - Spacing values (padding, gap)
   - Icons referenced
   - Child components / hierarchy

---

## Step 2 — Map Figma values to PIE

Before writing any code, translate the raw Figma values from your inventory into
PIE equivalents. Use the **`pie-design-system` skill** for every lookup — do not
invent token names or component props.

| What you found in Figma            | What to do                                                                                                                                                                             |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A colour value                     | Use `pie-design-system` → _Design tokens_ to find the matching alias token (e.g. `--dt-color-interactive-brand`). **Only use alias tokens, never global tokens.**                      |
| A spacing/gap/padding value        | Use `pie-design-system` → _Design tokens_ to find the `--dt-spacing-*` alias                                                                                                           |
| A border radius                    | Use `pie-design-system` → _Design tokens_ to find the `--dt-radius-*` alias                                                                                                            |
| A UI element (button, input, etc.) | Use `pie-design-system` → _Looking up components_ to identify the right `<pie-*>` element and its props                                                                                |
| An icon                            | Use `pie-design-system` → _Icons_ to find the correct `<icon-*>` element name. List `node_modules/@justeattakeaway/pie-icons-webc/icons/` to browse available names — never invent one |
| Typography                         | Use `pie-design-system` → _Typography_ and prefer utility classes from `pie-css` over raw font tokens                                                                                  |

Run the `pie-design-system` **bootstrap** before any of the above lookups to
ensure component and token reference files are current.

---

## Step 2.5 — Common components layer

Before writing any feature code, find the common components folder and assess
which UI elements from the inventory already have wrappers, which would benefit
from one, and which don't need one at all.

Not every PIE component needs a common wrapper — the value of wrapping comes
from reuse and project-specific concerns. A one-off `<pie-divider>` used once
in a layout doesn't need a wrapper. A `<pie-button>` used across dozens of
features does — it earns a wrapper that centralises the import, exposes typed
props, and adds conveniences like Vuelidate integration or icon slots.

### Find the common components folder

Glob for `src/components/common/` (or equivalent: `shared/`, `base/`, `ui/`).
Build a map of what exists and what PIE element each wrapper covers.

### Assess each UI element in the inventory

For each element, ask yourself: **would a common wrapper add meaningful value
here?** A wrapper is worth creating when one or more of the following is true:

- The component appears multiple times across the design (or is likely to
  across the wider codebase)
- The project adds something on top of the raw PIE component — validation
  integration, `defineModel` two-way binding, additional slots, default prop
  values that match the project's design language
- The component is a core interaction primitive (form inputs, buttons, modals,
  toggles) where consistency really matters

A wrapper is probably **not** worth creating when:

- The PIE component is used exactly once and carries no project-specific logic
- The component is purely structural/layout (e.g. `<pie-divider>`) with no
  props the project needs to standardise
- The raw PIE element is expressive enough on its own and wrapping it would add
  no real value

| Situation                                                       | Action                                                                       |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| A common wrapper already covers this element                    | Use it — `import ComponentName from '@/components/common/ComponentName.vue'` |
| A wrapper exists but is missing a prop or slot the design needs | Extend the existing wrapper, then use it                                     |
| No wrapper exists and one would add value (see criteria above)  | Ask the user before proceeding (see below)                                   |
| No wrapper exists and one would add little value                | Use the PIE element directly — note it in your summary                       |

**Icons are the exception** — use `<icon-*>` custom elements directly in
feature components. They are not wrapped in `common/` and don't need to be.

### Asking the user about missing wrappers

When you judge that a wrapper would be worth creating, pause and present your
reasoning. Group all proposed wrappers into a single question rather than
asking one at a time:

> "Before building, I'd suggest creating these common components:
>
> - `Notification.vue` — wraps `<pie-notification>`; used in 3 places in this
>   design and likely reused elsewhere
> - `Badge.vue` — wraps `<pie-tag>`; standardises the variant/size defaults
>   used throughout the design
>
> Should I create these first, or would you prefer to use the PIE elements
> directly for now?"

If the user says yes, create the wrappers first then continue to Step 3.
If the user says no, use the raw PIE elements and note them in your summary.

### Common wrapper conventions

When creating a new wrapper, follow the patterns established in the codebase:

- **File:** `src/components/common/{Name}.vue` — semantic name, not
  `Pie`-prefixed (e.g. `Badge.vue` not `PieTag.vue`)
- **Script:** `<script setup lang="ts">` with a typed `interface Props`,
  `withDefaults`, and `defineModel` for any two-way binding
- **PIE import:** the `@justeattakeaway/pie-webc/components/*.js` side-effect
  import goes inside the wrapper — never in the consuming feature component
- **Slots:** expose named slots where the underlying PIE component supports them
- **Tokens:** use `--dt-*` alias tokens in `<style scoped>` — no hardcoded
  values

---

## Step 3 — Component build loop

Build in leaf-first order: atoms (common wrappers, icons) before molecules
(form fields, cards) before page-level templates. This ensures each piece is
validated before it's composed into something larger.

Repeat the following cycle for each component:

### a. Write the component

- Import from `@/components/common/` — **never** import `@justeattakeaway/pie-webc`
  directly in a feature component (PIE imports belong in the common wrappers)
- Use `<icon-*>` custom elements directly for icons, with the import in the
  component that uses them
- Use `--dt-*` alias tokens for all colour, spacing, radius, and typography
- Run the `pie-design-system` **pre-flight checklist** before considering the
  component file done

**Large components — split into sub-components:**

Before writing, judge whether the component will be large. If the template is
likely to exceed ~150 lines, or contains clearly distinct logical sections
(e.g. a header, a body form, and a footer action bar), split it into separate
files rather than writing one monolithic component. Each sub-component should
have a single, named responsibility (e.g. `CampaignFormHeader.vue`,
`CampaignFormBody.vue`). The parent component then composes them. This is not
about hitting a line count threshold mechanically — it's about whether a reader
would benefit from the separation. If in doubt, split.

### b. Make it reachable

Ensure the component is visible at a navigable URL. Use an existing route if
possible. If not, add a temporary dev preview route or story — remove it once
the full page is assembled in Step 4.

### c. Navigate

```
chrome-devtools_navigate_page → dev server URL + preview route
```

Wait for the page to settle before screenshotting (HMR can introduce a brief
lag after a file save).

### d. Screenshot and show

```
chrome-devtools_take_screenshot
```

**Always attach the screenshot inline in your response.** The user needs to see
it so they can interrupt and redirect before you move on to the next component.
Narrate what you're about to compare so the user understands what to look for.

### e. Visual comparison

Use your vision to compare the screenshot against the Figma frame. Check:

| Aspect             | What to look for                                                                |
| ------------------ | ------------------------------------------------------------------------------- |
| **Layout**         | Flex/grid direction, alignment, relative positions of children                  |
| **Spacing**        | Padding and gap proportions — does it feel like the Figma spacing scale?        |
| **Colour roles**   | CTA background = interactive-brand, body text = content-default, etc.           |
| **Typography**     | Font weight, approximate size, family                                           |
| **Icons**          | Correct `<icon-*>` element, correct size variant (default 24px vs `Large` 32px) |
| **PIE components** | Correct `<pie-*>` element used, correct variant/size props                      |

**What to tolerate:** sub-pixel rendering differences, anti-aliasing variation,
dev-mode font loading vs Figma-rendered fonts, image optimisation differences.

### f. Report

State clearly what matches and what doesn't. Be specific about discrepancies
(e.g. "button uses `outline` variant but Figma shows `primary`", "gap between
label and input is too large — should map to `--dt-spacing-b` not `--dt-spacing-d`").

### g. Fix and re-validate

If issues were found, fix the code and re-screenshot. Repeat up to the number
of passes agreed at the start (default 5). If a discrepancy persists after all
passes are exhausted, note it, explain why (e.g. no matching PIE token, missing
component variant), and move on rather than getting stuck.

### h. Proceed

Mark the component done and move to the next item in the inventory.

> **User interrupt:** Every screenshot is shown inline before the next component
> begins. The user can stop, correct, or redirect at any point — this is
> intentional. If the user interjects, address their feedback before continuing
> the loop.

---

## Step 4 — Full-page validation

Once all components are assembled on the real application route:

1. Remove any temporary preview routes added in Step 3b.
2. Navigate Chrome to the real route.
3. Take a full-page screenshot (`fullPage: true` if the content is taller than
   the viewport).
4. Show the screenshot to the user.
5. Compare it against the top-level Figma frame using the same visual checklist
   from Step 3e.
6. Summarise: what matches, what still has gaps, and any known limitations
   (missing PIE component variant, awaiting design token, etc.).

---

## Reference

### Config file locations

| Agent       | MCP config path                                                                 |
| ----------- | ------------------------------------------------------------------------------- |
| OpenCode    | `~/.config/opencode/opencode.jsonc` → `mcp` object                              |
| Claude Code | `~/.claude/settings.json` → `mcpServers` object, or `.mcp.json` in project root |

### MCP server key names (as configured on this machine)

| MCP             | Key in config     |
| --------------- | ----------------- |
| Figma           | `figma`           |
| Chrome DevTools | `chrome-devtools` |

### Setup links

| Resource                              | URL                                                                                   |
| ------------------------------------- | ------------------------------------------------------------------------------------- |
| PIE agentic resources (skill install) | https://pie.design/agents/resources/                                                  |
| Figma MCP setup guide                 | https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server |
| Chrome DevTools MCP setup guide       | https://github.com/ChromeDevTools/chrome-devtools-mcp                                 |
| PIE Storybook / component docs        | https://webc.pie.design                                                               |

