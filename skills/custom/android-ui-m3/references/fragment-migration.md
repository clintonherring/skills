# Fragment Migration Guide — XML to Compose

Step-by-step guide for migrating OpenSAR Companion fragments from XML Views to Jetpack Compose, one fragment at a time.

---

## Table of Contents

1. [Migration Strategy](#migration-strategy)
2. [Prerequisites — Gradle Setup](#prerequisites--gradle-setup)
3. [Per-Fragment Migration Steps](#per-fragment-migration-steps)
4. [ComposeView Bridge Pattern](#composeview-bridge-pattern)
5. [Navigation Migration](#navigation-migration)
6. [Common Pitfalls](#common-pitfalls)
7. [Recommended Migration Order](#recommended-migration-order)

---

## Migration Strategy

**Incremental migration**: Convert one fragment at a time. XML and Compose coexist during migration. Each fragment is independently deployable after migration.

**Approach**: Use `ComposeView` inside existing Fragment classes as a bridge. This preserves the existing navigation graph and Fragment lifecycle while swapping the UI layer.

**Final state**: Once all fragments are migrated, convert to Compose Navigation and remove Fragment dependency entirely.

---

## Prerequisites — Gradle Setup

Add Compose support to the existing project. In `app/build.gradle.kts`:

```kotlin
android {
    buildFeatures {
        compose = true
        viewBinding = true // keep during migration
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14" // match Kotlin 1.9.24
    }
}

dependencies {
    // Compose BOM
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)

    // Core Compose
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")

    // Compose integration with Fragments
    implementation("androidx.fragment:fragment-compose:1.8.5")

    // Compose + Lifecycle
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")

    // Compose + Navigation (for later full migration)
    implementation("androidx.navigation:navigation-compose:2.8.5")

    // Material 3 Adaptive
    implementation("androidx.compose.material3.adaptive:adaptive:1.1.0")
    implementation("androidx.compose.material3.adaptive:adaptive-layout:1.1.0")
    implementation("androidx.compose.material3.adaptive:adaptive-navigation:1.1.0")

    // Google Maps Compose
    implementation("com.google.maps.android:maps-compose:6.2.1")

    // Window size classes
    implementation("androidx.compose.material3:material3-window-size-class")

    // Hilt (if adopting DI)
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")

    // Debug tooling
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
```

---

## Per-Fragment Migration Steps

For each fragment, follow this sequence:

### Step 1: Create the Composable Screen

Create a new `@Composable` function that replaces the XML layout. Place it alongside the Fragment file.

```
ui/pilot/
├── PilotCompanionFragment.kt      // existing — will be modified
├── PilotCompanionScreen.kt        // NEW — Compose screen
└── PilotCompanionViewModel.kt     // existing — may need Flow migration
```

```kotlin
// PilotCompanionScreen.kt
@Composable
fun PilotCompanionScreen(
    viewModel: PilotCompanionViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    // Compose UI implementation using M3 canonical layout
}
```

### Step 2: Update the Fragment to Use ComposeView

Replace `onCreateView` XML inflation with `ComposeView`:

**Before (XML):**
```kotlin
class PilotCompanionFragment : BaseProtectedFragment() {
    private var _binding: FragmentPilotCompanionBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentPilotCompanionBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        // setup listeners, observers, etc.
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
```

**After (ComposeView bridge):**
```kotlin
class PilotCompanionFragment : BaseProtectedFragment() {

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        return ComposeView(requireContext()).apply {
            setViewCompositionStrategy(
                ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed
            )
            setContent {
                OpenSARTheme {
                    PilotCompanionScreen()
                }
            }
        }
    }
}
```

### Step 3: Migrate ViewModel State to StateFlow

If the ViewModel uses `LiveData`, migrate to `StateFlow`:

**Before:**
```kotlin
class PilotCompanionViewModel : ViewModel() {
    private val _members = MutableLiveData<List<TeamMember>>()
    val members: LiveData<List<TeamMember>> = _members
}
```

**After:**
```kotlin
class PilotCompanionViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(PilotUiState())
    val uiState: StateFlow<PilotUiState> = _uiState.asStateFlow()
}
```

Collect in Compose with `collectAsStateWithLifecycle()`.

### Step 4: Remove XML Layout File

After verifying the Compose screen works correctly, delete the corresponding XML layout:

```
DELETE: res/layout/fragment_pilot_companion.xml
```

### Step 5: Update Navigation Graph (if needed)

The navigation graph entry stays the same during bridge migration — it still references the Fragment class. No changes needed until the full navigation migration.

---

## ComposeView Bridge Pattern

This is the critical pattern that enables incremental migration:

```kotlin
abstract class ComposeFragment : BaseProtectedFragment() {

    @Composable
    abstract fun Content()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View = ComposeView(requireContext()).apply {
        setViewCompositionStrategy(
            ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed
        )
        setContent {
            OpenSARTheme {
                Content()
            }
        }
    }
}
```

Migrated fragments extend `ComposeFragment` and implement `Content()`:

```kotlin
class PilotCompanionFragment : ComposeFragment() {
    @Composable
    override fun Content() {
        PilotCompanionScreen()
    }
}
```

---

## Navigation Migration

### Phase 1: Bridge (during fragment migration)

- Keep `mobile_navigation.xml` as-is
- Each fragment uses `ComposeView` internally
- Navigation actions still use `findNavController().navigate()`

### Phase 2: Full Compose Navigation (after all fragments migrated)

Replace the XML navigation graph with Compose Navigation:

```kotlin
@Composable
fun OpenSARNavHost(navController: NavHostController) {
    NavHost(navController = navController, startDestination = "login") {
        composable("login") { LoginScreen() }
        composable("companion_selection") { CompanionSelectionScreen() }
        composable("pilot") { PilotCompanionScreen() }
        composable("ground_team") { GroundTeamCompanionScreen() }
        composable("controller") { ControllerCompanionScreen() }
        composable("viewer") { ViewerCompanionScreen() }
        composable("create_search") { CreateSearchPartyScreen() }
        composable("manage_search") { ManageSearchScreen() }
        composable("wayline_list") { WaylineListDetailScreen() }
        composable("wayline_edit/{waylineId}") { backStackEntry ->
            WaylineEditScreen(waylineId = backStackEntry.arguments?.getString("waylineId") ?: "")
        }
        composable("settings") { SettingsScreen() }
        composable("diagnostics") { DiagnosticsScreen() }
    }
}
```

---

## Common Pitfalls

### 1. ViewCompositionStrategy

Always set `DisposeOnViewTreeLifecycleDestroyed`. Without it, Compose may leak or not recompose properly in Fragment lifecycle.

### 2. Fullscreen / Immersive Mode

The current app uses immersive mode for Pilot/GroundTeam. In Compose, handle with:

```kotlin
val systemUiController = rememberSystemUiController()
LaunchedEffect(Unit) {
    systemUiController.isSystemBarsVisible = false
    systemUiController.systemBarsBehavior =
        SystemBarsBehavior.SHOW_TRANSIENT_BARS_BY_SWIPE
}
```

Or use `enableEdgeToEdge()` in the Activity and handle insets per-screen.

### 3. Google Maps View vs Compose

The existing app uses Maps SDK Views. The Compose `GoogleMap` composable wraps the same underlying `MapView` but provides a Compose-native API. Camera state, markers, and properties all have Compose equivalents. Do NOT mix View-based MapView and Compose GoogleMap in the same screen.

### 4. Permission Handling

Keep permission requests in the Fragment/Activity layer during bridge migration. Use `rememberLauncherForActivityResult` when fully on Compose.

### 5. Safe Args

Safe Args generates code for Fragment navigation. During bridge phase, keep using them. In Phase 2, replace with Compose Navigation arguments.

---

## Recommended Migration Order

Migrate in this order — simplest first, building confidence before tackling complex map screens:

| Priority | Fragment | Complexity | Notes |
|----------|----------|-----------|-------|
| 1 | SettingsFragment | Low | Simple form, no map |
| 2 | DiagnosticsFragment | Low | Read-only display |
| 3 | LoginFragment | Low | Form + auth logic |
| 4 | SignUpFragment | Low | Form + validation |
| 5 | ConsentFragment | Low | Static content + checkbox |
| 6 | CompanionSelectionFragment | Low | Selection grid |
| 7 | FunctionSelectionFragment | Low | Button list |
| 8 | WaylineListFragment | Medium | List → ListDetailPaneScaffold |
| 9 | ManageSearchFragment | Medium | List → ListDetailPaneScaffold |
| 10 | ViewerCompanionFragment | Medium | Map (read-only) → SupportingPaneScaffold |
| 11 | CreateSearchPartyFragment | High | Map + form → SupportingPaneScaffold |
| 12 | GroundTeamCompanionFragment | High | Map + team → SupportingPaneScaffold |
| 13 | ControllerCompanionFragment | High | Map + devices → SupportingPaneScaffold |
| 14 | PilotCompanionFragment | High | Map + flight → SupportingPaneScaffold |
| 15 | WaylineEditFragment | High | Map + editing → SupportingPaneScaffold |

Also migrate dialog fragments when their parent is migrated:
- ChangeStatusDialogFragment → Compose `AlertDialog`
- JoinSearchDialogFragment → Compose `AlertDialog` or `ModalBottomSheet`
