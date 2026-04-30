# Canonical Layouts — Implementation Guide

M3 canonical layouts are pre-designed, adaptable structures for common app patterns. Use them as the foundation for every screen.

Sources:
- [M3 Canonical Layouts](https://m3.material.io/foundations/layout/canonical-layouts/overview)
- [Android Canonical Layouts — Compose](https://developer.android.com/develop/ui/compose/layouts/adaptive/canonical-layouts) — Official implementation guidance with samples
- [Build a supporting pane layout](https://developer.android.com/develop/ui/compose/layouts/adaptive/build-a-supporting-pane-layout)
- [Build a list-detail layout](https://developer.android.com/develop/ui/compose/layouts/adaptive/build-a-list-detail-layout)
- [Material 3 Design Kit (devrath)](https://github.com/devrath/Material-3-Design-Kit) — Code samples for M3 components in Compose

---

## Table of Contents

1. [Supporting Pane (Map Screens)](#supporting-pane)
2. [List-Detail (List Screens)](#list-detail)
3. [Feed Layout](#feed-layout)
4. [Implementation Guidance from Android Docs](#implementation-guidance)
5. [Dependencies](#dependencies)
6. [OpenSAR Fragment Mapping](#opensar-fragment-mapping)

---

## Supporting Pane

**Use for all map-centric screens.** The main pane holds the map; the supporting pane holds controls, lists, and status.

### Behavior by Width

| Width Class | Layout |
|-------------|--------|
| Compact (< 600dp) | Map fullscreen + bottom sheet for supporting content |
| Medium (600–839dp) | Map 60% + supporting pane 40%, side by side |
| Expanded (840dp+) | Map 65% + supporting pane 35%, side by side |

### Implementation

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun MapSupportingPaneScreen(
    viewModel: MapScreenViewModel = hiltViewModel()
) {
    val navigator = rememberSupportingPaneScaffoldNavigator()
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    SupportingPaneScaffold(
        directive = navigator.scaffoldDirective,
        value = navigator.scaffoldValue,
        mainPane = {
            // Main pane: Google Map
            MapMainPane(
                uiState = uiState,
                onMarkerClick = { viewModel.selectMarker(it) }
            )
        },
        supportingPane = {
            // Supporting pane: controls, lists, status
            AnimatedPane {
                SupportingContent(
                    uiState = uiState,
                    onAction = { viewModel.handleAction(it) }
                )
            }
        },
        extraPane = null // Optional third pane for detail views
    )
}
```

### Map Main Pane Pattern

```kotlin
@Composable
fun MapMainPane(
    uiState: MapUiState,
    onMarkerClick: (MarkerId) -> Unit
) {
    Box(modifier = Modifier.fillMaxSize()) {
        // Full-bleed map
        GoogleMap(
            modifier = Modifier.fillMaxSize(),
            cameraPositionState = uiState.cameraPosition,
            properties = MapProperties(
                mapType = uiState.mapType,
                isMyLocationEnabled = uiState.locationEnabled
            ),
            uiSettings = MapUiSettings(
                zoomControlsEnabled = false, // custom controls
                myLocationButtonEnabled = false
            )
        ) {
            // Markers, polylines, polygons
            uiState.markers.forEach { marker ->
                Marker(
                    state = MarkerState(position = marker.position),
                    title = marker.title,
                    onClick = { onMarkerClick(marker.id); true }
                )
            }
        }

        // Glass overlay: search bar at top
        GlassSearchBar(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = 8.dp, start = 16.dp, end = 16.dp)
                .statusBarsPadding()
        )

        // Floating controls: zoom, location, layers
        FloatingMapControls(
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(end = 16.dp)
        )
    }
}
```

### Supporting Pane Content Pattern

```kotlin
@Composable
fun SupportingContent(
    uiState: MapUiState,
    onAction: (UiAction) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        // Section header
        Text(
            text = "Team Status",
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier.padding(bottom = 8.dp)
        )

        // Content cards
        uiState.teamMembers.forEach { member ->
            TeamMemberCard(
                member = member,
                onClick = { onAction(UiAction.SelectMember(member.id)) }
            )
            Spacer(modifier = Modifier.height(8.dp))
        }
    }
}
```

### Compact Fallback: Bottom Sheet

On compact screens where `SupportingPaneScaffold` shows only the main pane, provide a bottom sheet for the supporting content:

```kotlin
@Composable
fun CompactMapScreen(
    uiState: MapUiState,
    onAction: (UiAction) -> Unit
) {
    val sheetState = rememberBottomSheetScaffoldState(
        bottomSheetState = rememberStandardBottomSheetState(
            initialValue = SheetValue.PartiallyExpanded
        )
    )

    BottomSheetScaffold(
        scaffoldState = sheetState,
        sheetPeekHeight = 56.dp, // minimal peek showing drag handle
        sheetContainerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f),
        sheetContent = {
            SupportingContent(uiState = uiState, onAction = onAction)
        }
    ) {
        MapMainPane(uiState = uiState, onMarkerClick = { /* ... */ })
    }
}
```

---

## List-Detail

**Use for list-based screens** that navigate to a detail view.

### Behavior by Width

| Width Class | Layout |
|-------------|--------|
| Compact | List screen → navigate to detail screen |
| Medium | List 40% + detail 60% side by side |
| Expanded | List 35% + detail 65% side by side |

### Implementation

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun WaylineListDetailScreen(
    viewModel: WaylineListViewModel = hiltViewModel()
) {
    val navigator = rememberListDetailPaneScaffoldNavigator<WaylineId>()
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    ListDetailPaneScaffold(
        directive = navigator.scaffoldDirective,
        value = navigator.scaffoldValue,
        listPane = {
            AnimatedPane {
                WaylineList(
                    waylines = uiState.waylines,
                    selectedId = uiState.selectedId,
                    onSelect = { id ->
                        viewModel.select(id)
                        navigator.navigateTo(ListDetailPaneScaffoldRole.Detail, id)
                    }
                )
            }
        },
        detailPane = {
            AnimatedPane {
                navigator.currentDestination?.content?.let { id ->
                    WaylineDetail(waylineId = id)
                }
            }
        }
    )
}
```

---

## Feed Layout

**Use for**: settings, diagnostics, and any scrollable single-column content.

```kotlin
@Composable
fun FeedScreen(content: @Composable ColumnScope.() -> Unit) {
    val windowSizeClass = calculateWindowSizeClass(LocalContext.current as Activity)
    val maxWidth = when (windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Compact -> Dp.Infinity
        WindowWidthSizeClass.Medium -> 600.dp
        else -> 840.dp
    }

    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.TopCenter
    ) {
        LazyColumn(
            modifier = Modifier.widthIn(max = maxWidth),
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            content = { item { Column(content = content) } }
        )
    }
}
```

---

## Implementation Guidance

Key implementation principles from the [Android developer docs](https://developer.android.com/develop/ui/compose/layouts/adaptive/canonical-layouts):

### Supporting Pane — Android Docs Summary

- Primary display area occupies ~2/3 of the app window; supporting pane takes the remainder
- Works well on **expanded-width** displays in landscape orientation
- On medium/compact widths: supporting content goes in a **bottom sheet** or **side sheet** accessible via a control
- Differs from list-detail: supporting content is **meaningful only in relation** to the primary content (e.g., a tool palette for a map)
- Hoist all state (window size class, main content data, supporting content data) for unidirectional data flow
- Compact: supporting content **below** main content or in a bottom sheet
- Medium: split display space **equally** (50/50)
- Expanded: **70% main / 30% supporting**

### List-Detail — Android Docs Summary

- Divides window into two side-by-side panes: list + detail
- Expanded-width: both visible simultaneously
- Medium/compact-width: shows either list or detail based on user interaction
- Selection of a list item updates detail pane; back press restores list
- Configuration changes (rotation, resize) preserve state:
  - Expanded narrowing to compact → detail stays visible, list hidden
  - Compact widening to expanded → both shown, list indicates selected item
- Use `BackHandler` for compact/medium to navigate from detail back to list (not part of overall app navigation)

### Feed — Android Docs Summary

- Arranges equivalent content elements in a configurable grid
- Size and position establish relationships among elements
- Cards and lists are common components
- Adapts from single scrolling column to multi-column grid
- Use `LazyVerticalGrid` with min column width; configure `maxLineSpan` for full-width items (headers, dividers)
- On compact width with insufficient space for multiple columns, behaves like `LazyColumn`

### M3 Color System Reference

From the [Material 3 Design Kit](https://github.com/devrath/Material-3-Design-Kit):

| Color Role | Purpose |
|-----------|---------|
| **Primary** | Bright, stands out — action buttons, CTAs |
| **Secondary** | Based on primary, stands out less — secondary actions |
| **Tertiary** | Lighter still — tertiary actions |
| **On Primary** | Content color on top of primary (icon/text on a primary button) |
| **Primary Container** | Background for FABs, chips, selections |
| **On Primary Container** | Content color on primary container |
| **Surface** | Card/list item backgrounds |
| **On Surface** | Content on surface |
| **Background** | Screen background, padding areas between surfaces |
| **Error / On Error** | Error states (snackbar bg / snackbar text) |
| **Error Container / On Error Container** | Error dialogs (bg / content) |
| **Inverse** | Elements displayed on top of other surfaces (snackbar) |
| **Neutral Variant** | Borders, outlines, subtle content dividers |

Dynamic colors (Android 12+) generate themes from wallpaper. Can be disabled for brand-specific palettes. See `dynamicLightColorScheme(context)` / `dynamicDarkColorScheme(context)`.

---

## Dependencies

Add to `libs.versions.toml`:

```toml
[versions]
compose-material3-adaptive = "1.1.0"
maps-compose = "6.2.1"

[libraries]
material3-adaptive = { group = "androidx.compose.material3.adaptive", name = "adaptive", version.ref = "compose-material3-adaptive" }
material3-adaptive-layout = { group = "androidx.compose.material3.adaptive", name = "adaptive-layout", version.ref = "compose-material3-adaptive" }
material3-adaptive-navigation = { group = "androidx.compose.material3.adaptive", name = "adaptive-navigation", version.ref = "compose-material3-adaptive" }
maps-compose = { group = "com.google.maps.android", name = "maps-compose", version.ref = "maps-compose" }
```

Add to `build.gradle.kts`:

```kotlin
dependencies {
    implementation(libs.material3.adaptive)
    implementation(libs.material3.adaptive.layout)
    implementation(libs.material3.adaptive.navigation)
    implementation(libs.maps.compose)
}
```

---

## OpenSAR Fragment Mapping

Which canonical layout each fragment should use:

| Fragment | Canonical Layout | Main Pane | Supporting Pane |
|----------|-----------------|-----------|-----------------|
| PilotCompanionFragment | **Supporting Pane** | Google Map (flight area, aircraft, team) | Flight controls, altitude, telemetry, team status |
| GroundTeamCompanionFragment | **Supporting Pane** | Google Map (search area, team positions) | Team list, status updates, assignment controls |
| CreateSearchPartyFragment | **Supporting Pane** | Google Map (area selection) | Search party config form, member list |
| ControllerCompanionFragment | **Supporting Pane** | Google Map (overview) | Connected devices, mission controls |
| ViewerCompanionFragment | **Supporting Pane** | Google Map (read-only view) | Status panel, legend |
| WaylineListFragment | **List-Detail** | Wayline list | Wayline map preview + edit |
| WaylineEditFragment | **Supporting Pane** | Google Map (wayline edit) | Waypoint properties, actions |
| ManageSearchFragment | **List-Detail** | Search party list | Search detail + map |
| SettingsFragment | **Feed** | Settings form (single column) | — |
| DiagnosticsFragment | **Feed** | Diagnostics info (single column) | — |
| LoginFragment | **Feed** | Login form (centered, max-width) | — |
| SignUpFragment | **Feed** | Sign-up form (centered, max-width) | — |
| CompanionSelectionFragment | **Feed** | Selection grid/list | — |
| FunctionSelectionFragment | **Feed** | Function buttons | — |
