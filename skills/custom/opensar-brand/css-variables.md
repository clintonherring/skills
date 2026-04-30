# CSS Custom Properties

Standalone CSS variables for use outside MUI components (plain CSS, map overlays, custom widgets).

## Light Mode Variables

```css
:root {
  /* Core Neutrals */
  --osar-midnight: #1a2332;
  --osar-navy-slate: #2c3e50;
  --osar-storm: #546e7a;
  --osar-pewter: #90a4ae;
  --osar-ash: #cfd8dc;
  --osar-mist: #eceff1;
  --osar-cloud: #f5f7fa;
  --osar-white: #ffffff;

  /* Primary Blue */
  --osar-blue: #1565c0;
  --osar-blue-dark: #0d47a1;
  --osar-blue-light: #42a5f5;
  --osar-blue-bg: #e3f2fd;

  /* Operational Status */
  --osar-warning: #f57f17;
  --osar-warning-bg: #fff8e1;
  --osar-critical: #c62828;
  --osar-critical-bg: #ffebee;
  --osar-success: #2e7d32;
  --osar-success-bg: #e8f5e9;
  --osar-info: #1565c0;
  --osar-info-bg: #e3f2fd;

  /* Typography */
  --osar-font-sans: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --osar-font-mono: 'JetBrains Mono', 'Fira Code', 'Source Code Pro', monospace;

  /* Spacing */
  --osar-space-xs: 4px;
  --osar-space-sm: 8px;
  --osar-space-md: 16px;
  --osar-space-lg: 24px;
  --osar-space-xl: 32px;
  --osar-space-2xl: 48px;

  /* Radii */
  --osar-radius-sm: 4px;
  --osar-radius-md: 8px;
  --osar-radius-lg: 12px;
  --osar-radius-round: 9999px;

  /* Elevation */
  --osar-shadow-1: 0 1px 3px rgba(26, 35, 50, 0.08);
  --osar-shadow-2: 0 4px 12px rgba(26, 35, 50, 0.10);
  --osar-shadow-3: 0 8px 24px rgba(26, 35, 50, 0.14);
  --osar-shadow-4: 0 16px 48px rgba(26, 35, 50, 0.18);

  /* Semantic aliases */
  --osar-text-primary: var(--osar-midnight);
  --osar-text-secondary: var(--osar-storm);
  --osar-text-disabled: var(--osar-pewter);
  --osar-bg-page: var(--osar-cloud);
  --osar-bg-surface: var(--osar-white);
  --osar-bg-sidebar: var(--osar-navy-slate);
  --osar-border: var(--osar-ash);
  --osar-accent: var(--osar-blue);
  --osar-accent-hover: var(--osar-blue-dark);
  --osar-accent-bg: var(--osar-blue-bg);
}
```

## Dark Mode Variables

```css
[data-theme="dark"],
.dark-mode {
  --osar-midnight: #e2e8f0;
  --osar-navy-slate: #a0aec0;
  --osar-storm: #718096;
  --osar-pewter: #4a5568;
  --osar-ash: #2d3748;
  --osar-mist: #1c2433;
  --osar-cloud: #161b22;
  --osar-white: #1c2433;

  /* Primary Blue (Dark) */
  --osar-blue: #42a5f5;
  --osar-blue-dark: #1565c0;
  --osar-blue-light: #64b5f6;
  --osar-blue-bg: #1a3a5c;

  /* Operational Status (Dark) */
  --osar-warning: #ffb74d;
  --osar-warning-bg: #3e2723;
  --osar-critical: #ef5350;
  --osar-critical-bg: #3b1515;
  --osar-success: #66bb6a;
  --osar-success-bg: #1b3a1b;
  --osar-info: #42a5f5;
  --osar-info-bg: #1a3a5c;

  /* Elevation (Dark - no shadows, use borders) */
  --osar-shadow-1: none;
  --osar-shadow-2: none;
  --osar-shadow-3: none;
  --osar-shadow-4: none;

  /* Semantic aliases auto-adapt via variable references */
  --osar-bg-page: #0d1117;
  --osar-bg-surface: #1c2433;
  --osar-bg-sidebar: #161b22;
}
```

## Usage Examples

### Map Controls Overlay

```css
.map-controls {
  position: absolute;
  top: var(--osar-space-sm);
  right: var(--osar-space-sm);
  z-index: 1000;
  background-color: var(--osar-bg-surface);
  padding: var(--osar-space-md);
  border-radius: var(--osar-radius-lg);
  box-shadow: var(--osar-shadow-2);
  font-family: var(--osar-font-sans);
  color: var(--osar-text-primary);
  opacity: 0.92;
  transition: opacity 0.2s ease;
}

.map-controls:hover {
  opacity: 1;
}
```

### Status Badge

```css
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--osar-space-xs);
  padding: 2px var(--osar-space-sm);
  border-radius: var(--osar-radius-round);
  font-family: var(--osar-font-sans);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.status-badge--active { color: var(--osar-warning); background: var(--osar-warning-bg); }
.status-badge--critical { color: var(--osar-critical); background: var(--osar-critical-bg); }
.status-badge--resolved { color: var(--osar-success); background: var(--osar-success-bg); }
.status-badge--info { color: var(--osar-info); background: var(--osar-info-bg); }
```

### Flight Path (Map SVG)

```css
.flight-path {
  stroke: var(--osar-blue);
  stroke-width: 3;
  fill: none;
}

.flight-area {
  stroke: var(--osar-critical);
  stroke-width: 2;
  fill: var(--osar-critical-bg);
  fill-opacity: 0.3;
}

.search-zone {
  stroke: var(--osar-warning);
  stroke-width: 2;
  fill: var(--osar-warning-bg);
  fill-opacity: 0.2;
}
```
