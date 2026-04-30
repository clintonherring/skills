# Compose UI Patterns

Reusable Jetpack Compose patterns for OpenSAR map-based SAR app. All patterns follow M3 design tokens and the 6-3-1 color rule.

Additional component examples: [Material 3 Design Kit](https://github.com/devrath/Material-3-Design-Kit) — Buttons, TextFields, Selection UI, Tab Rows, Toolbars, Bottom Navigation, Bottom Sheets, Dialogs, Drawers.

---

## Table of Contents

1. [Glass Panel Modifier](#glass-panel-modifier)
2. [Glass Search Bar](#glass-search-bar)
3. [Floating Map Controls](#floating-map-controls)
4. [Status Card](#status-card)
5. [Team Member Card](#team-member-card)
6. [Adaptive Navigation Shell](#adaptive-navigation-shell)
7. [Bottom Sheet on Map](#bottom-sheet-on-map)
8. [ViewModel + StateFlow Pattern](#viewmodel--stateflow-pattern)
9. [Theme Setup](#theme-setup)
10. [Performance Guidelines](#performance-guidelines)

---

## Glass Panel Modifier

Semi-transparent surface that floats over the map. Creates depth without fully occluding map content.

```kotlin
@Composable
fun Modifier.glassPanel(
    alpha: Float = 0.72f,
    shape: Shape = MaterialTheme.shapes.large
): Modifier {
    val surfaceColor = MaterialTheme.colorScheme.surface
    return this
        .then(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                Modifier.blur(20.dp)
            } else {
                Modifier // graceful degradation: no blur pre-Android 12
            }
        )
        .background(
            color = surfaceColor.copy(alpha = alpha),
            shape = shape
        )
        .border(
            width = 0.5.dp,
            color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.3f),
            shape = shape
        )
}
```

Usage:
```kotlin
Box(
    modifier = Modifier
        .fillMaxWidth()
        .glassPanel()
        .padding(16.dp)
) {
    Text("Overlay content", style = MaterialTheme.typography.bodyLarge)
}
```

---

## Glass Search Bar

Top search bar for map screens. Floats over the map with glass effect.

```kotlin
@Composable
fun GlassSearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onSearch: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    SearchBar(
        inputField = {
            SearchBarDefaults.InputField(
                query = query,
                onQueryChange = onQueryChange,
                onSearch = onSearch,
                expanded = false,
                onExpandedChange = {},
                leadingIcon = {
                    Icon(Icons.Default.Search, contentDescription = "Search")
                },
                placeholder = {
                    Text("Search area...", style = MaterialTheme.typography.bodyLarge)
                }
            )
        },
        expanded = false,
        onExpandedChange = {},
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp),
        colors = SearchBarDefaults.colors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.80f)
        ),
        tonalElevation = 0.dp,
        shadowElevation = 2.dp
    ) {}
}
```

---

## Floating Map Controls

Vertical column of floating action buttons for map interaction (zoom, location, layers).

```kotlin
@Composable
fun FloatingMapControls(
    onZoomIn: () -> Unit,
    onZoomOut: () -> Unit,
    onMyLocation: () -> Unit,
    onLayerToggle: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        SmallFloatingActionButton(
            onClick = onLayerToggle,
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f),
            contentColor = MaterialTheme.colorScheme.onSurface
        ) {
            Icon(Icons.Default.Layers, contentDescription = "Toggle layers")
        }

        SmallFloatingActionButton(
            onClick = onMyLocation,
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f),
            contentColor = MaterialTheme.colorScheme.primary
        ) {
            Icon(Icons.Default.MyLocation, contentDescription = "My location")
        }

        // Zoom cluster
        Surface(
            shape = MaterialTheme.shapes.medium,
            color = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f),
            tonalElevation = 2.dp
        ) {
            Column {
                IconButton(onClick = onZoomIn) {
                    Icon(Icons.Default.Add, contentDescription = "Zoom in")
                }
                HorizontalDivider(
                    modifier = Modifier.width(32.dp),
                    color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)
                )
                IconButton(onClick = onZoomOut) {
                    Icon(Icons.Default.Remove, contentDescription = "Zoom out")
                }
            }
        }
    }
}
```

---

## Map Overlay Chips (Google Maps Pattern)

Floating `AssistChip` row for map-centric screens. Positioned `TopStart` with `statusBarsPadding()` so they clear system bars while the map draws edge-to-edge behind them.

**M3 Assist Chip Specs** (from [chips/specs](https://m3.material.io/components/chips/specs)):

| Attribute | Spec Value |
|-----------|-----------|
| Height | 32dp |
| Shape | 8dp corner radius |
| Icon size | 18dp |
| Left/right padding (no icon) | 16dp |
| Left/right padding (with icon) | 8dp |
| Padding between elements | 8dp |
| Default container color | `surfaceContainerLow` (optional) |
| Label color | `onSurface` |
| Outline color | `outline` |

**Design rules** (from [chips/guidelines](https://m3.material.io/components/chips/guidelines) and [chips/overview](https://m3.material.io/components/chips/overview)):
- **Text-only labels** -- omit leading icons unless the icon conveys information the label cannot. "Pilot" and "Ground Team" are self-explanatory; adding a mode icon wastes horizontal space.
- **Keep chip row narrow** -- the row shares the status-bar zone with a floating avatar button at `TopEnd`. Three short chips is the practical maximum before overlap.
- **Semi-transparent container** -- use `surfaceContainerHigh.copy(alpha = 0.92f)` for map overlays so the chip is readable over any map tile without fully occluding it. This overrides the default `surfaceContainerLow` because map tiles need higher contrast.
- **Alert coloring** -- use `errorContainer` / `onErrorContainer` for chips that convey active state requiring attention (e.g., "Location shared").
- **Concise labels, sentence case** -- per M3 Expressive (May 2025), keep labels short and use sentence case.
- **Do not override height** -- the 32dp spec height keeps the row compact on map surfaces.

```kotlin
Row(
    modifier = Modifier
        .align(Alignment.TopStart)
        .statusBarsPadding()
        .padding(start = 16.dp, top = 8.dp),
    horizontalArrangement = Arrangement.spacedBy(8.dp)
) {
    // Mode/title chip -- text only, no leading icon
    AssistChip(
        onClick = onTitleClick,
        label = { Text(title, maxLines = 1) },
        colors = AssistChipDefaults.assistChipColors(
            containerColor = MaterialTheme.colorScheme
                .surfaceContainerHigh.copy(alpha = 0.92f)
        )
    )
    // Alert chip -- location sharing active
    if (locationSharingText != null) {
        StatusChip(
            text = locationSharingText,
            icon = Icons.Filled.LocationOn,
            alert = true,
            onClick = onLocationSharingClick
        )
    }
    // Contextual chip -- search party status
    if (statusChipText != null) {
        StatusChip(text = statusChipText, onClick = onStatusChipClick)
    }
}
```

The shell's `AvatarButton` occupies `TopEnd` with matching `statusBarsPadding()`. Because chips grow from the left and the avatar is pinned right, they never collide as long as labels stay short.

---

## Status Card

Compact card for displaying status information (team member, device, search party).

```kotlin
@Composable
fun StatusCard(
    title: String,
    subtitle: String,
    statusColor: Color,
    statusLabel: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    leadingIcon: @Composable (() -> Unit)? = null
) {
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceContainerLow
        )
    ) {
        Row(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            leadingIcon?.invoke()

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // Status badge
            Surface(
                shape = MaterialTheme.shapes.small,
                color = statusColor.copy(alpha = 0.15f)
            ) {
                Text(
                    text = statusLabel,
                    style = MaterialTheme.typography.labelSmall,
                    color = statusColor,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
    }
}
```

---

## Team Member Card

Specialized card for SAR team member display.

```kotlin
@Composable
fun TeamMemberCard(
    name: String,
    role: String,
    status: MemberStatus,
    lastUpdate: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val statusColor = when (status) {
        MemberStatus.ACTIVE -> MaterialTheme.colorScheme.primary
        MemberStatus.IDLE -> MaterialTheme.colorScheme.tertiary
        MemberStatus.OFFLINE -> MaterialTheme.colorScheme.outline
        MemberStatus.ALERT -> MaterialTheme.colorScheme.error
    }

    StatusCard(
        title = name,
        subtitle = "$role  •  $lastUpdate",
        statusColor = statusColor,
        statusLabel = status.label,
        onClick = onClick,
        modifier = modifier,
        leadingIcon = {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .background(
                        color = statusColor.copy(alpha = 0.12f),
                        shape = CircleShape
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = null,
                    tint = statusColor,
                    modifier = Modifier.size(24.dp)
                )
            }
        }
    )
}
```

---

## Adaptive Navigation Shell

App-level shell that switches navigation pattern based on window width.

```kotlin
@Composable
fun OpenSARNavigationShell(
    currentDestination: NavDestination?,
    onNavigate: (Route) -> Unit,
    content: @Composable () -> Unit
) {
    val windowSizeClass = calculateWindowSizeClass(LocalContext.current as Activity)

    when (windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Compact -> {
            Scaffold(
                bottomBar = {
                    NavigationBar {
                        navigationItems.forEach { item ->
                            NavigationBarItem(
                                selected = currentDestination?.route == item.route,
                                onClick = { onNavigate(item.route) },
                                icon = { Icon(item.icon, contentDescription = item.label) },
                                label = { Text(item.label) }
                            )
                        }
                    }
                }
            ) { innerPadding ->
                Box(Modifier.padding(innerPadding)) { content() }
            }
        }
        WindowWidthSizeClass.Medium -> {
            Row(Modifier.fillMaxSize()) {
                NavigationRail {
                    navigationItems.forEach { item ->
                        NavigationRailItem(
                            selected = currentDestination?.route == item.route,
                            onClick = { onNavigate(item.route) },
                            icon = { Icon(item.icon, contentDescription = item.label) },
                            label = { Text(item.label) }
                        )
                    }
                }
                Box(Modifier.weight(1f)) { content() }
            }
        }
        else -> {
            PermanentNavigationDrawer(
                drawerContent = {
                    PermanentDrawerSheet(Modifier.width(240.dp)) {
                        navigationItems.forEach { item ->
                            NavigationDrawerItem(
                                label = { Text(item.label) },
                                selected = currentDestination?.route == item.route,
                                onClick = { onNavigate(item.route) },
                                icon = { Icon(item.icon, contentDescription = item.label) }
                            )
                        }
                    }
                }
            ) {
                content()
            }
        }
    }
}
```

---

## Bottom Sheet on Map

For compact screens where the supporting pane collapses to a bottom sheet.

```kotlin
@Composable
fun MapWithBottomSheet(
    mapContent: @Composable () -> Unit,
    sheetContent: @Composable ColumnScope.() -> Unit
) {
    BottomSheetScaffold(
        sheetPeekHeight = 64.dp,
        sheetContainerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.90f),
        sheetShape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
        sheetDragHandle = {
            Surface(
                modifier = Modifier.padding(vertical = 8.dp),
                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.4f),
                shape = MaterialTheme.shapes.extraLarge
            ) {
                Box(Modifier.size(width = 32.dp, height = 4.dp))
            }
        },
        sheetContent = sheetContent
    ) {
        mapContent()
    }
}
```

---

## ViewModel + StateFlow Pattern

Standard pattern for all screen ViewModels.

```kotlin
data class PilotUiState(
    val isLoading: Boolean = true,
    val cameraPosition: CameraPositionState = CameraPositionState(),
    val mapType: MapType = MapType.NORMAL,
    val teamMembers: List<TeamMember> = emptyList(),
    val selectedMemberId: String? = null,
    val error: String? = null
)

sealed interface PilotUiAction {
    data class SelectMember(val id: String) : PilotUiAction
    data class UpdateMapType(val type: MapType) : PilotUiAction
    data object RefreshTeam : PilotUiAction
    data object CenterOnSelf : PilotUiAction
}

@HiltViewModel
class PilotCompanionViewModel @Inject constructor(
    private val teamRepository: TeamRepository,
    private val locationProvider: LocationProvider
) : ViewModel() {

    private val _uiState = MutableStateFlow(PilotUiState())
    val uiState: StateFlow<PilotUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            teamRepository.observeTeam()
                .catch { e -> _uiState.update { it.copy(error = e.message) } }
                .collect { members ->
                    _uiState.update { it.copy(teamMembers = members, isLoading = false) }
                }
        }
    }

    fun onAction(action: PilotUiAction) {
        when (action) {
            is PilotUiAction.SelectMember ->
                _uiState.update { it.copy(selectedMemberId = action.id) }
            is PilotUiAction.UpdateMapType ->
                _uiState.update { it.copy(mapType = action.type) }
            PilotUiAction.RefreshTeam -> refreshTeam()
            PilotUiAction.CenterOnSelf -> centerOnSelf()
        }
    }

    private fun refreshTeam() { /* ... */ }
    private fun centerOnSelf() { /* ... */ }
}
```

---

## Theme Setup

OpenSAR M3 theme with dynamic color support.

```kotlin
@Composable
fun OpenSARTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> darkColorScheme(
            primary = Color(0xFF90CAF9),       // OpenSAR blue light
            secondary = Color(0xFFA5D6A7),     // OpenSAR green light
            surface = Color(0xFF1C1B1F),
            surfaceContainer = Color(0xFF2B2930)
        )
        else -> lightColorScheme(
            primary = Color(0xFF2196F3),       // OpenSAR blue
            secondary = Color(0xFF4CAF50),     // OpenSAR green
            surface = Color(0xFFFFFBFE),
            surfaceContainer = Color(0xFFF3EDF7)
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = OpenSARTypography,
        shapes = OpenSARShapes,
        content = content
    )
}

val OpenSARTypography = Typography(
    headlineMedium = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 28.sp,
        lineHeight = 36.sp
    ),
    titleLarge = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 22.sp,
        lineHeight = 28.sp
    ),
    titleMedium = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp,
        lineHeight = 24.sp
    ),
    bodyLarge = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp
    ),
    labelLarge = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp
    )
)

val OpenSARShapes = Shapes(
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(24.dp)
)
```

---

## Performance Guidelines

Target: **90+ fps** on all screens.

1. **State reads**: Use `derivedStateOf` for computed values; avoid recomposing entire trees
2. **Lists**: Always use `LazyColumn`/`LazyRow` with stable keys
3. **Map markers**: Use `MapEffect` for bulk marker operations; avoid recomposition per marker
4. **Images**: Use `AsyncImage` (Coil) with proper sizing and caching
5. **Blur**: Only apply blur to static/slow-changing backgrounds, never to scrolling content
6. **Remember**: Wrap expensive computations in `remember {}` or `rememberSaveable {}`
7. **Stability**: Mark UI state classes as `@Stable` or `@Immutable` for Compose compiler optimizations
