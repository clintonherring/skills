---
name: android-ui-m3
description: Design and build Android UI following Material 3 layout principles, glassmorphism, and modern map-app patterns. Use when creating or refactoring Android fragments/layouts, implementing Jetpack Compose UI, designing adaptive layouts for phone/tablet/foldable, working with Google Maps Compose, applying M3 canonical layouts (supporting pane, list-detail), migrating XML layouts to Compose, or when the user mentions Android UI, Material 3, M3, fragment layout, map UI, or adaptive layout.
---

# Android UI — Material 3

Modern Android UI skill for OpenSAR Companion and similar map-based SAR apps. Covers M3 layout, Jetpack Compose, adaptive design, and fragment-by-fragment migration from XML to Compose.

## MANDATORY: Spec-Check Before Any Component Work

**Before suggesting, implementing, or modifying ANY M3 component**, you MUST follow this workflow:

### Step 0: Understand Intent

**Ask the user what they are trying to achieve** before jumping to a component recommendation. The correct M3 component depends on the user's goal, not just what exists in the code today. For example:
- "Navigate back" could be a TopAppBar navigation icon, a bottom nav item, or a system back gesture
- "Show status" could be a chip, a badge, a snackbar, or a banner
- "Trigger an action" could be a button, FAB, icon button, or chip depending on context

If the user's intent is ambiguous or multiple components could fit, present the options with trade-offs and let the user choose.

### Step 1: Identify Component Type

Determine which M3 component(s) are involved (e.g., Button, Chip, TopAppBar, NavigationBar, BottomSheet, Dialog, Card, etc.)

### Step 2: Fetch ALL Three M3 Design Spec Pages

For each component, read all three pages from `m3.material.io`. Each page serves a different purpose:

| Page | URL Pattern | What It Tells You |
|------|------------|-------------------|
| **Overview** | `https://m3.material.io/components/{component}/overview` | Variants, anatomy, when to use |
| **Guidelines** | `https://m3.material.io/components/{component}/guidelines` | Usage rules, dos/don'ts, placement, behavior, accessibility |
| **Specs** | `https://m3.material.io/components/{component}/specs` | Exact dimensions, padding, color tokens, typography tokens, elevation |

Use the [M3 Components Index](#m3-components-index) below to find the correct base URL, then append `/overview`, `/guidelines`, and `/specs`.

### Step 3: Fetch MDC-Android Implementation Doc

Read the implementation guidance from `https://raw.githubusercontent.com/material-components/material-components-android/master/docs/components/{Component}.md`. Use the [MDC-Android Docs Index](#mdc-android-docs-index) below to find the correct filename. This gives you the correct API classes, XML attributes, Compose parameters, and theming hooks.

### Step 4: Cross-Reference

Verify your proposed usage against:
- **Guidelines** -- correct variant for the use case, correct placement, correct behavior
- **Specs** -- correct dimensions, color tokens, typography tokens, elevation
- **Implementation doc** -- correct API, attributes, theming

### Step 5: Cite

When presenting your suggestion to the user, briefly note which spec informed the decision. Examples:
- "Per the M3 App Bars guidelines, a small top app bar is recommended for screens with limited scrolling"
- "Per the M3 Chips specs, assist chips have a height of 32dp and use `surfaceContainerLow` as the default container color"
- "Per the MDC-Android Chip.md, use `app:chipIconTint` to set the leading icon color"

**Never rely on memory alone for M3 component behavior.** The specs are the source of truth. This prevents incorrect variants, wrong color tokens, missing accessibility attributes, and non-standard usage patterns.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| UI Framework | Jetpack Compose (not XML Views) |
| State Management | Kotlin Flow + StateFlow |
| Design System | Material 3 + M3 Expressive |
| Maps | Google Maps Compose (`maps-compose`) |
| Adaptive Layout | `material3-adaptive` (SupportingPaneScaffold, ListDetailPaneScaffold) |
| Architecture | Single Activity, Fragment-per-feature, MVVM with ViewModel |
| Navigation | Jetpack Navigation (Compose variant) |

## Core Visual Principles

### 1. Layered Depth & Glassmorphism

Apply glass-like surfaces over map content to create spatial depth:

```kotlin
fun Modifier.glassBackground(
    alpha: Float = 0.65f,
    blurRadius: Dp = 20.dp
): Modifier = this
    .blur(blurRadius)
    .background(
        MaterialTheme.colorScheme.surface.copy(alpha = alpha),
        shape = MaterialTheme.shapes.large
    )
    .border(
        width = 0.5.dp,
        color = MaterialTheme.colorScheme.outline.copy(alpha = 0.2f),
        shape = MaterialTheme.shapes.large
    )
```

- Use semi-transparent `surface` over map for panels, bottom sheets, search bars
- For Android 12+: use `Modifier.blur()`; below 12: use `RenderScript` fallback or skip blur
- Keep foreground content (text, icons) fully opaque for readability

### 2. Color — 6-3-1 Rule

| Proportion | Role | M3 Token |
|-----------|------|----------|
| 60% dominant | Background/map | `surface`, `surfaceContainer` |
| 30% secondary | Cards, panels, sheets | `surfaceContainerHigh`, `secondaryContainer` |
| 10% accent | CTAs, active states, FABs | `primary`, `tertiary` |

Always derive colors from `MaterialTheme.colorScheme`. Never hardcode hex values.

### 3. Typography — Adaptive & Hierarchical

Use M3 type roles based on content hierarchy, not visual size:

| Content | Type Role |
|---------|----------|
| Screen/page title | `headlineMedium` |
| Section header | `titleLarge` |
| Card title | `titleMedium` |
| Body content | `bodyLarge` |
| Labels, captions | `labelMedium` / `labelSmall` |
| Map overlay info | `labelLarge` with glass background |

### 4. Spatial UI — Floating Controls (Orbiters)

For map-centric screens, use floating controls that don't obscure the map:

- FABs and mini-FABs positioned at screen edges
- Expandable bottom sheets (peek height ~56dp)
- Collapsible top search bars that hide on scroll
- Side rail navigation on tablets (medium/expanded width)

## M3 Layout System

### Spacing Grid

**8dp baseline grid** for all spacing. Use 4dp for tight adjustments (icon padding).

| Context | Value |
|---------|-------|
| Screen edge margin (compact) | 16dp |
| Screen edge margin (medium+) | 24dp |
| Content padding inside cards | 16dp |
| Space between content areas | 8dp |
| List item height (minimum) | 56dp |
| Touch target minimum | 48dp × 48dp |

### Window Size Classes

| Class | Width | Panes | Nav Pattern |
|-------|-------|-------|-------------|
| Compact | < 600dp | 1 | Bottom nav or modal drawer |
| Medium | 600–839dp | 1–2 | Navigation rail |
| Expanded | 840–1199dp | 2 | Navigation rail + permanent drawer |
| Large | 1200–1599dp | 2–3 | Permanent drawer |

Detect with `calculateWindowSizeClass()` in Compose.

### Parts of Layout

Every screen has these M3 structural regions:

1. **Navigation** — app-level nav (bottom bar, rail, drawer)
2. **Body** — primary content area (the map, the list)
3. **Pane** — secondary content alongside body (supporting pane)

For detailed spacing, density, and hardware considerations, see [references/m3-layout.md](references/m3-layout.md).

## Canonical Layouts

### Map Fragments → Supporting Pane

**Use for**: PilotCompanionFragment, GroundTeamCompanionFragment, CreateSearchPartyFragment, and any map-centric screen.

```
┌─────────────────────────────────────┐
│  TopAppBar / Search Bar             │
├────────────────────┬────────────────┤
│                    │                │
│    Main Pane       │  Supporting    │
│    (Google Map)    │  Pane          │
│                    │  (controls,    │
│                    │   team list,   │
│                    │   status)      │
│                    │                │
├────────────────────┴────────────────┤
│  Bottom Bar (contextual actions)    │
└─────────────────────────────────────┘
```

On compact screens, the supporting pane collapses to a bottom sheet.

### List Screens → List-Detail

**Use for**: WaylineListFragment, ManageSearchFragment, search party lists.

On expanded screens: list on left, detail on right. On compact: list navigates to detail.

### Content Browsing → Feed

**Use for**: Activity feeds, notification lists, media galleries, any scrollable collection of equivalent content items.

```
┌─────────────────────────────────────┐
│  TopAppBar / Filters                │
├─────────────────────────────────────┤
│ ┌───────┐ ┌───────┐ ┌───────┐      │
│ │ Card  │ │ Card  │ │ Card  │      │
│ └───────┘ └───────┘ └───────┘      │
│ ┌───────┐ ┌───────┐ ┌───────┐      │
│ │ Card  │ │ Card  │ │ Card  │      │
│ └───────┘ └───────┘ └───────┘      │
├─────────────────────────────────────┤
│  Bottom Bar                         │
└─────────────────────────────────────┘
```

On compact: single-column list or 2-column grid. On medium+: multi-column grid. Implement with `LazyVerticalGrid` or `LazyVerticalStaggeredGrid`. Content is typically dynamic (API-driven) and rendered in Cards or Tiles.

For implementation code and patterns, see [references/canonical-layouts.md](references/canonical-layouts.md).

## Fragment-Based Architecture

### Encapsulation

Each feature = one Composable screen + one ViewModel:

```kotlin
@Composable
fun PilotCompanionScreen(
    viewModel: PilotCompanionViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    // Self-contained screen with its own state
}
```

### SSOT — Single Source of Truth

- UI state flows from ViewModel → Composable (unidirectional)
- User events flow from Composable → ViewModel
- ViewModel holds `StateFlow<UiState>` as the single source

### Loose Coupling

- Fragments/screens communicate via shared ViewModels or Navigation arguments
- Never pass Fragment references between screens
- Use `SavedStateHandle` for navigation arguments

### Dynamic Multi-Pane

Use `SupportingPaneScaffold` or `ListDetailPaneScaffold` — they automatically adapt:
- Compact: single pane with navigation
- Medium/Expanded: side-by-side panes
- Foldable: respects hinge/fold position

## Migration Strategy (XML → Compose)

Migrate one fragment at a time using `ComposeView` bridge:

1. Create `@Composable` screen function
2. Replace Fragment's `onCreateView` XML inflation with `ComposeView`
3. Move logic from Fragment into ViewModel (if not already)
4. Remove XML layout file after migration
5. Update navigation graph

For step-by-step guide and code, see [references/fragment-migration.md](references/fragment-migration.md).

## Compose Code Patterns

For reusable code patterns including glass panels, map overlays, adaptive scaffolds, and bottom sheets, see [references/compose-patterns.md](references/compose-patterns.md).

## M3 Components Index

For each component, fetch ALL THREE pages. The base URL pattern is `https://m3.material.io/components/{slug}/` followed by `overview`, `guidelines`, or `specs`.

| Component | URL Slug (append to base) |
|-----------|--------------------------|
| App bars (Top/Bottom) | `app-bars` |
| Badges | `badges` |
| Bottom sheets | `bottom-sheets` |
| Button groups | `button-groups` |
| Buttons | `buttons` |
| Cards | `cards` |
| Carousel | `carousel` |
| Checkbox | `checkbox` |
| Chips | `chips` |
| Date pickers | `date-pickers` |
| Dialogs | `dialogs` |
| Divider | `divider` |
| Extended FABs | `extended-fab` |
| FAB menu | `fab-menu` |
| Floating action buttons | `floating-action-button` |
| Icon buttons | `icon-buttons` |
| Lists | `lists` |
| Loading indicator | `loading-indicator` |
| Menus | `menus` |
| Navigation bar | `navigation-bar` |
| Navigation drawer | `navigation-drawer` |
| Navigation rail | `navigation-rail` |
| Progress indicators | `progress-indicators` |
| Radio button | `radio-button` |
| Search | `search` |
| Segmented buttons | `segmented-buttons` |
| Side sheets | `side-sheets` |
| Sliders | `sliders` |
| Snackbar | `snackbar` |
| Split button | `split-button` |
| Switch | `switch` |
| Tabs | `tabs` |
| Text fields | `text-fields` |
| Time pickers | `time-pickers` |
| Toolbars | `toolbars` |
| Tooltips | `tooltips` |

**Example for Chips**: fetch all three:
- `https://m3.material.io/components/chips/overview`
- `https://m3.material.io/components/chips/guidelines`
- `https://m3.material.io/components/chips/specs`

## MDC-Android Docs Index

Use these URLs to fetch the Android implementation doc before coding any component. Pattern: `https://raw.githubusercontent.com/material-components/material-components-android/master/docs/components/{File}.md`

| Component | Implementation Doc Filename |
|-----------|----------------------------|
| Badge | `BadgeDrawable.md` |
| Banner | `Banner.md` |
| Bottom app bar | `BottomAppBar.md` |
| Bottom navigation | `BottomNavigation.md` |
| Bottom sheet | `BottomSheet.md` |
| Button (index) | `Button.md` |
| Button (common) | `CommonButton.md` |
| Button group | `ButtonGroup.md` |
| Card | `Card.md` |
| Carousel | `Carousel.md` |
| Checkbox | `Checkbox.md` |
| Chip | `Chip.md` |
| Data table | `DataTable.md` |
| Date picker | `DatePicker.md` |
| Dialog | `Dialog.md` |
| Divider | `Divider.md` |
| Docked floating toolbars | `DockedFloatingToolbars.md` |
| Docked toolbar | `DockedToolbar.md` |
| Extended FAB | `ExtendedFloatingActionButton.md` |
| FAB | `FloatingActionButton.md` |
| FAB menu | `FloatingActionButtonMenu.md` |
| Floating toolbar | `FloatingToolbar.md` |
| Icon button | `IconButton.md` |
| Image list | `ImageList.md` |
| List | `List.md` |
| Loading indicator | `LoadingIndicator.md` |
| Material text view | `MaterialTextView.md` |
| Menu | `Menu.md` |
| Navigation drawer | `NavigationDrawer.md` |
| Navigation rail | `NavigationRail.md` |
| Overflow linear layout | `OverflowLinearLayout.md` |
| Progress indicator | `ProgressIndicator.md` |
| Radio button | `RadioButton.md` |
| Search | `Search.md` |
| Side sheet | `SideSheet.md` |
| Slider | `Slider.md` |
| Snackbar | `Snackbar.md` |
| Split button | `SplitButton.md` |
| Switch | `Switch.md` |
| Tabs | `Tabs.md` |
| Text field | `TextField.md` |
| Time picker | `TimePicker.md` |

The [MDC-Android catalog app](https://github.com/material-components/material-components-android/tree/master/catalog) provides runnable code samples for each component.

## External References

### Authoritative Sources (always consult before component work)
- [M3 Components Hub](https://m3.material.io/components) — All M3 component design specs (overview, guidelines, specs)
- [MDC-Android Component Docs](https://github.com/material-components/material-components-android/tree/master/docs/components) — Android implementation guides, attributes, theming for every component
- [MDC-Android Catalog App](https://github.com/material-components/material-components-android/tree/master/catalog) — Runnable code samples for each component

### Layout & Adaptive
- [Android Canonical Layouts — Design Guide](https://developer.android.com/design/ui/mobile/guides/layout-and-content/canonical-layouts) — Mobile design guidance for list-detail, feed, and supporting pane patterns
- [Android Canonical Layouts — Compose](https://developer.android.com/develop/ui/compose/layouts/adaptive/canonical-layouts) — Official implementation guidance with supporting pane, list-detail, and feed samples
- [M3 Layout Foundations](https://m3.material.io/foundations/layout/understanding-layout/overview) — Spacing, density, parts of layout, hardware, RTL
- [M3 Canonical Layouts](https://m3.material.io/foundations/layout/canonical-layouts/overview) — Design guidance for canonical patterns
- [M3 Window Size Classes](https://m3.material.io/foundations/layout/applying-layout/window-size-classes) — Breakpoint definitions

### Other
- [Material 3 Design Kit](https://github.com/devrath/Material-3-Design-Kit) — M3 component code samples (Buttons, TextFields, Tabs, Sheets, Dialogs, Drawers, Color System, Typography, Shapes, Elevation)
- [Maps Compose Library](https://developers.google.com/maps/documentation/android-sdk/maps-compose) — Google Maps SDK for Compose

## Checklist — Before Submitting a Layout

- [ ] **Spec-checked**: Fetched M3 design spec AND MDC-Android implementation doc for every component used
- [ ] Uses `MaterialTheme.colorScheme` tokens (no hardcoded colors)
- [ ] Uses `MaterialTheme.typography` roles (no hardcoded text styles)
- [ ] Spacing follows 8dp grid
- [ ] Touch targets ≥ 48dp
- [ ] Screen edge margins: 16dp (compact) / 24dp (medium+)
- [ ] Adapts to compact/medium/expanded via window size classes
- [ ] Map fragments use SupportingPaneScaffold
- [ ] List fragments use ListDetailPaneScaffold
- [ ] Feed/gallery screens use LazyVerticalGrid with adaptive columns
- [ ] Glass/translucent overlays on map surfaces
- [ ] 6-3-1 color proportion respected
- [ ] RTL layout support verified
- [ ] Content descriptions on all interactive elements (accessibility)
