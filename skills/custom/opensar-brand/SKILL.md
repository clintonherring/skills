---
name: opensar-brand
description: Applies OpenSAR brand identity (colors, typography, spacing, components) to web frontends and artifacts. Based on Modern Minimalist with aviation-blue SAR accents. Use when styling OpenSAR web components, creating MUI themes, building dashboards, designing UI for the OpenSAR platform, or when brand consistency is needed across OpenSAR frontends.
---

# OpenSAR Brand Identity

Mission-critical drone management for Search and Rescue. Clean minimalist design reduces cognitive load during high-stress SAR operations. The blue-slate palette evokes aviation trust and operational authority.

## Brand Philosophy

- **Clarity over decoration** -- operators use this in the field
- **Status at a glance** -- color conveys operational meaning instantly
- **Consistent across surfaces** -- mobile frontend, desktop frontend, pilot UI

## Color System

### Light Mode

**Core Neutrals:**

| Token | Hex | Usage |
|-------|-----|-------|
| `midnight` | `#1a2332` | Primary text, dark headings |
| `navy-slate` | `#2c3e50` | Secondary text, sidebar background |
| `storm` | `#546e7a` | Tertiary text, icons |
| `pewter` | `#90a4ae` | Placeholder text, disabled states |
| `ash` | `#cfd8dc` | Borders, dividers |
| `mist` | `#eceff1` | Table stripes, subtle backgrounds |
| `cloud` | `#f5f7fa` | Page background |
| `white` | `#ffffff` | Card surfaces, inputs |

**Primary Blue:**

| Token | Hex | Usage |
|-------|-----|-------|
| `sar-blue` | `#1565c0` | Primary actions, links, active nav |
| `deep-blue` | `#0d47a1` | Hover states, focus rings |
| `ice-blue` | `#e3f2fd` | Selected backgrounds, badges |

**Operational Status:**

| Status | Foreground | Background | Usage |
|--------|-----------|------------|-------|
| Warning | `#f57f17` | `#fff8e1` | Active missions, caution |
| Critical | `#c62828` | `#ffebee` | Emergencies, alerts |
| Success | `#2e7d32` | `#e8f5e9` | Mission complete, resolved |
| Info | `#1565c0` | `#e3f2fd` | Informational notices |

### Dark Mode

**Core Neutrals:**

| Token | Hex | Usage |
|-------|-----|-------|
| `void` | `#0d1117` | Deepest background |
| `obsidian` | `#161b22` | Page background |
| `charcoal` | `#1c2433` | Card surfaces |
| `graphite` | `#2d3748` | Elevated surfaces, inputs |
| `zinc` | `#4a5568` | Borders, dividers |
| `steel` | `#718096` | Secondary text, icons |
| `silver` | `#a0aec0` | Primary text |
| `frost` | `#e2e8f0` | Headings, emphasis |

**Primary Blue (Dark):**

| Token | Hex | Usage |
|-------|-----|-------|
| `sky-blue` | `#42a5f5` | Primary actions (lighter for dark bg) |
| `light-blue` | `#64b5f6` | Hover states |
| `navy-glow` | `#1a3a5c` | Selected backgrounds |

**Operational Status (Dark):**

| Status | Foreground | Background | Usage |
|--------|-----------|------------|-------|
| Warning | `#ffb74d` | `#3e2723` | Active missions, caution |
| Critical | `#ef5350` | `#3b1515` | Emergencies, alerts |
| Success | `#66bb6a` | `#1b3a1b` | Mission complete, resolved |
| Info | `#42a5f5` | `#1a3a5c` | Informational notices |

## Typography

| Role | Font | Weight | Fallback Stack |
|------|------|--------|----------------|
| Headings | Inter | 600, 700 | 'Segoe UI', Roboto, Helvetica, Arial, sans-serif |
| Body | Inter | 400, 500 | 'Segoe UI', Roboto, Helvetica, Arial, sans-serif |
| Mono | JetBrains Mono | 400, 500 | 'Fira Code', 'Source Code Pro', monospace |

**Google Fonts import:**
```
https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap
```

### Type Scale

| Level | Size | Weight | Line Height | Letter Spacing |
|-------|------|--------|-------------|----------------|
| H1 | 2rem (32px) | 700 | 1.2 | -0.02em |
| H2 | 1.5rem (24px) | 700 | 1.3 | -0.01em |
| H3 | 1.25rem (20px) | 600 | 1.4 | 0 |
| H4 | 1.125rem (18px) | 600 | 1.4 | 0 |
| Body 1 | 1rem (16px) | 400 | 1.6 | 0 |
| Body 2 | 0.875rem (14px) | 400 | 1.5 | 0.01em |
| Caption | 0.75rem (12px) | 500 | 1.4 | 0.03em |
| Overline | 0.625rem (10px) | 600 | 1.6 | 0.08em |

## Shape and Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 4px | Chips, badges, toggles |
| `radius-md` | 8px | Buttons, inputs, selects |
| `radius-lg` | 12px | Cards, dialogs, panels |
| `radius-round` | 9999px | Avatars, status dots |
| `space-unit` | 8px | Base spacing unit |
| `space-xs` | 4px | Tight gaps |
| `space-sm` | 8px | Inline spacing |
| `space-md` | 16px | Component padding |
| `space-lg` | 24px | Section gaps |
| `space-xl` | 32px | Page sections |
| `space-2xl` | 48px | Major separations |

## Elevation (Light Mode)

Use box-shadows with the `midnight` color at varying opacity:

| Level | Shadow | Usage |
|-------|--------|-------|
| 0 | none | Flat elements |
| 1 | `0 1px 3px rgba(26,35,50,0.08)` | Cards at rest |
| 2 | `0 4px 12px rgba(26,35,50,0.10)` | Cards on hover, dropdowns |
| 3 | `0 8px 24px rgba(26,35,50,0.14)` | Dialogs, popovers |
| 4 | `0 16px 48px rgba(26,35,50,0.18)` | Modals |

**Dark mode elevation**: Use background color shift instead of shadows. Each elevation step lightens the surface by one neutral tier.

## Component Patterns

### Sidebar
- Background: `navy-slate` (light) / `obsidian` (dark)
- Active item: `sar-blue` text with `ice-blue` / `navy-glow` background
- Icons: `pewter` default, `sar-blue` / `sky-blue` when active
- Width: 240px collapsed-capable to 64px

### Status Badges
- Pill shape (`radius-round`), uppercase `caption` typography
- Use operational status foreground on matching background
- Always include text label -- never color-only

### Map Controls
- White / `charcoal` card surfaces with `radius-lg`
- Elevation level 2
- Semi-transparent when idle: 90% opacity, 100% on hover

### Data Tables
- Header: `mist` / `graphite` background, `storm` / `silver` text, `caption` weight
- Alternating rows: `white`-`cloud` / `obsidian`-`charcoal`
- Row hover: `ice-blue` / `navy-glow`

## Additional Resources

- For a ready-to-use MUI `createTheme` config, see [mui-theme.md](mui-theme.md)
- For CSS custom properties, see [css-variables.md](css-variables.md)
