# Material 3 Layout Reference

Detailed M3 layout specifications for spacing, density, window size classes, parts of layout, hardware considerations, and bidirectionality.

Sources: [M3 Layout Overview](https://m3.material.io/foundations/layout/understanding-layout/overview), [Spacing](https://m3.material.io/foundations/layout/understanding-layout/spacing), [Density](https://m3.material.io/foundations/layout/understanding-layout/density), [Parts of Layout](https://m3.material.io/foundations/layout/understanding-layout/parts-of-layout), [Hardware](https://m3.material.io/foundations/layout/understanding-layout/hardware-considerations), [RTL](https://m3.material.io/foundations/layout/understanding-layout/bidirectionality-rtl), [Window Size Classes](https://m3.material.io/foundations/layout/applying-layout/window-size-classes)

---

## Table of Contents

1. [Spacing System](#spacing-system)
2. [Density](#density)
3. [Window Size Classes](#window-size-classes)
4. [Parts of Layout](#parts-of-layout)
5. [Hardware Considerations](#hardware-considerations)
6. [Bidirectionality (RTL)](#bidirectionality-rtl)

---

## Spacing System

### Baseline Grid

All spacing uses an **8dp baseline grid**. Iconography and small adjustments use **4dp**.

### Margin & Padding Reference

| Element | Compact (< 600dp) | Medium (600–839dp) | Expanded (840dp+) |
|---------|-------------------|--------------------|--------------------|
| Screen edge margin | 16dp | 24dp | 24dp |
| Content gutter | 8dp | 12dp | 16dp |
| Card internal padding | 16dp | 16dp | 24dp |
| Section spacing | 16dp | 24dp | 32dp |
| List item min height | 56dp | 56dp | 56dp |

### Fixed vs Flexible Spacing

- **Fixed spacing**: consistent regardless of screen size (e.g., icon-to-text gap = 8dp)
- **Flexible spacing**: scales with screen size (e.g., screen edge margins)
- Use `Arrangement.spacedBy()` in Compose for consistent gap control

### Compose Spacing Tokens

```kotlin
// Standard spacing scale (define once, use everywhere)
object Spacing {
    val xs = 4.dp    // tight adjustments, icon padding
    val sm = 8.dp    // between related items
    val md = 16.dp   // card padding, screen margin (compact)
    val lg = 24.dp   // section gaps, screen margin (medium+)
    val xl = 32.dp   // large section separation
    val xxl = 48.dp  // hero/feature spacing
}
```

---

## Density

### Touch Targets

- Minimum touch target: **48dp × 48dp** (accessibility requirement)
- Recommended touch target: **56dp × 56dp** for primary actions
- Visual size can be smaller than touch target — use `Modifier.minimumInteractiveComponentSize()`

### Density Levels

| Level | Use Case | List Item Height | Padding Scale |
|-------|----------|-----------------|---------------|
| Default | Most screens | 56dp | 1× |
| Comfortable | Touch-heavy, mobile | 64dp | 1.25× |
| Compact | Data-dense, desktop | 40dp | 0.75× |

### When to Adjust Density

- **Map overlays**: Use compact density to minimize map obstruction
- **Lists & forms**: Use default density
- **Touch-primary mobile**: Use comfortable density for finger-friendly targets
- **Tablets in landscape**: Can use compact density for more visible content

---

## Window Size Classes

### Width Breakpoints

| Class | Width Range | Typical Devices |
|-------|-------------|-----------------|
| Compact | < 600dp | 99.96% phones portrait |
| Medium | 600–839dp | 93.73% tablets portrait, large foldables |
| Expanded | 840–1199dp | 97.22% tablets landscape, large foldables landscape |
| Large | 1200–1599dp | Large tablets, small desktops |
| Extra-large | ≥ 1600dp | Desktop displays |

### Height Breakpoints

| Class | Height Range | Typical Devices |
|-------|-------------|-----------------|
| Compact | < 480dp | 99.78% phones landscape |
| Medium | 480–899dp | Tablets landscape, phones portrait |
| Expanded | ≥ 900dp | 94.25% tablets portrait |

### Implementation

```kotlin
@Composable
fun AdaptiveScreen() {
    val windowSizeClass = calculateWindowSizeClass(LocalContext.current as Activity)

    when (windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Compact -> CompactLayout()
        WindowWidthSizeClass.Medium -> MediumLayout()
        WindowWidthSizeClass.Expanded -> ExpandedLayout()
    }
}
```

### Navigation Pattern per Width

| Width Class | Navigation Component | Behavior |
|-------------|---------------------|----------|
| Compact | `NavigationBar` (bottom) | 3–5 destinations |
| Medium | `NavigationRail` (side) | Icons + optional labels |
| Expanded | `PermanentNavigationDrawer` | Full labels, always visible |

---

## Parts of Layout

Every M3 screen is composed of these structural regions:

### 1. Navigation Region
- Contains app-level navigation (bottom bar, rail, drawer)
- Consistent across the app
- Adapts based on window size class

### 2. App Bar Region
- Top app bar: title, navigation icon, actions
- Can be `SmallTopAppBar`, `MediumTopAppBar`, `LargeTopAppBar`
- For map screens: use transparent/glass app bar that overlays the map

### 3. Body Region
- Primary content area
- Scrollable in most cases
- For map screens: the GoogleMap composable fills this region

### 4. Supporting Pane Region
- Secondary content alongside the body
- Only visible on medium/expanded width
- Collapses to bottom sheet or separate screen on compact

### Layout Regions in Compose

```kotlin
Scaffold(
    topBar = { /* App Bar Region */ },
    bottomBar = { /* Navigation Region (compact) */ },
    floatingActionButton = { /* Orbiter / floating control */ }
) { innerPadding ->
    // Body Region
    Box(modifier = Modifier.padding(innerPadding)) {
        // Content
    }
}
```

---

## Hardware Considerations

### Foldables

- Respect the hinge/fold with `WindowInfoTracker`
- Avoid placing interactive elements on the fold
- Use `SupportingPaneScaffold` — it handles fold awareness automatically
- Test with Posture: tabletop mode and book mode

### Orientation Changes

- Preserve state across orientation changes via ViewModel
- Map camera position should persist
- Bottom sheet state should persist

### System Bars & Insets

```kotlin
Modifier
    .fillMaxSize()
    .systemBarsPadding()        // status bar + nav bar
    .displayCutoutPadding()     // notch/punch-hole
    .imePadding()               // keyboard
```

Material 3 composables handle insets automatically:
- `TopAppBar` → top + horizontal system bar padding
- `BottomAppBar` → bottom + horizontal padding
- `NavigationBar` → bottom padding
- `NavigationRail` → vertical padding

### Edge-to-Edge

All screens should use edge-to-edge rendering:

```kotlin
// In Activity.onCreate()
enableEdgeToEdge()
WindowCompat.setDecorFitsSystemWindows(window, false)
```

Map screens benefit most from edge-to-edge — the map extends behind system bars.

---

## Bidirectionality (RTL)

### Core Rules

- Use `start`/`end` instead of `left`/`right` for all layout directions
- Icons that indicate direction (arrows, navigation) must mirror in RTL
- Icons representing objects (search, settings) do NOT mirror
- Text alignment follows content language direction

### Compose RTL Support

```kotlin
// Automatic with CompositionLocalProvider
CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
    // Content renders RTL
}

// For individual modifiers
Modifier.padding(start = 16.dp, end = 8.dp)  // ✅ correct
Modifier.padding(PaddingValues(start = 16.dp))  // ✅ correct
// Modifier.absolutePadding(left = 16.dp)  // ❌ avoid unless intentional
```

### Map-Specific RTL

- Map controls (zoom, compass) stay in their platform position
- Search bars and panels follow RTL direction
- Coordinate displays remain LTR (numbers don't mirror)
