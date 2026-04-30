# MUI Theme Configuration

Drop-in `createTheme` config for both OpenSAR frontends. Supports light and dark mode via `palette.mode`.

## Font Setup

Add to `public/index.html` `<head>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## Light Theme

```javascript
import { createTheme } from '@mui/material/styles';

const opensarLight = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1565c0',
      dark: '#0d47a1',
      light: '#42a5f5',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#546e7a',
      dark: '#2c3e50',
      light: '#90a4ae',
      contrastText: '#ffffff',
    },
    error: {
      main: '#c62828',
      light: '#ffebee',
    },
    warning: {
      main: '#f57f17',
      light: '#fff8e1',
    },
    success: {
      main: '#2e7d32',
      light: '#e8f5e9',
    },
    info: {
      main: '#1565c0',
      light: '#e3f2fd',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
    },
    text: {
      primary: '#1a2332',
      secondary: '#546e7a',
      disabled: '#90a4ae',
    },
    divider: '#cfd8dc',
    action: {
      hover: 'rgba(21, 101, 192, 0.06)',
      selected: '#e3f2fd',
      disabled: '#90a4ae',
      disabledBackground: '#eceff1',
    },
  },
  typography: {
    fontFamily: "'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    h1: { fontSize: '2rem', fontWeight: 700, lineHeight: 1.2, letterSpacing: '-0.02em' },
    h2: { fontSize: '1.5rem', fontWeight: 700, lineHeight: 1.3, letterSpacing: '-0.01em' },
    h3: { fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.4 },
    h4: { fontSize: '1.125rem', fontWeight: 600, lineHeight: 1.4 },
    h5: { fontSize: '1rem', fontWeight: 600, lineHeight: 1.5 },
    h6: { fontSize: '0.875rem', fontWeight: 600, lineHeight: 1.5, letterSpacing: '0.01em' },
    body1: { fontSize: '1rem', fontWeight: 400, lineHeight: 1.6 },
    body2: { fontSize: '0.875rem', fontWeight: 400, lineHeight: 1.5, letterSpacing: '0.01em' },
    caption: { fontSize: '0.75rem', fontWeight: 500, lineHeight: 1.4, letterSpacing: '0.03em' },
    overline: { fontSize: '0.625rem', fontWeight: 600, lineHeight: 1.6, letterSpacing: '0.08em' },
    button: { fontWeight: 600, letterSpacing: '0.02em', textTransform: 'none' },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0 1px 3px rgba(26,35,50,0.08)',
    '0 2px 6px rgba(26,35,50,0.08)',
    '0 4px 12px rgba(26,35,50,0.10)',
    '0 6px 16px rgba(26,35,50,0.10)',
    '0 8px 24px rgba(26,35,50,0.14)',
    '0 12px 32px rgba(26,35,50,0.14)',
    '0 16px 48px rgba(26,35,50,0.18)',
    ...Array(17).fill('0 16px 48px rgba(26,35,50,0.18)'),
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#f5f7fa',
        },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: '#ffffff',
          color: '#1a2332',
          borderBottom: '1px solid #cfd8dc',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#2c3e50',
          color: '#90a4ae',
          borderRight: 'none',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 20px',
          fontWeight: 600,
        },
        containedPrimary: {
          '&:hover': { backgroundColor: '#0d47a1' },
        },
        outlinedPrimary: {
          borderColor: '#1565c0',
          '&:hover': { backgroundColor: '#e3f2fd', borderColor: '#0d47a1' },
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 1 },
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid #eceff1',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 4, fontWeight: 500 },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#eceff1',
            color: '#546e7a',
            fontWeight: 600,
            fontSize: '0.75rem',
            letterSpacing: '0.03em',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:nth-of-type(even)': { backgroundColor: '#f5f7fa' },
          '&:hover': { backgroundColor: '#e3f2fd' },
        },
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined', size: 'small' },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#1a2332',
          fontSize: '0.75rem',
          borderRadius: 4,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        standardError: { backgroundColor: '#ffebee', color: '#c62828' },
        standardWarning: { backgroundColor: '#fff8e1', color: '#f57f17' },
        standardSuccess: { backgroundColor: '#e8f5e9', color: '#2e7d32' },
        standardInfo: { backgroundColor: '#e3f2fd', color: '#1565c0' },
      },
    },
    MuiBox: {
      styleOverrides: {
        root: { boxSizing: 'border-box' },
      },
    },
  },
});
```

## Dark Theme

```javascript
const opensarDark = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#42a5f5',
      dark: '#1565c0',
      light: '#64b5f6',
      contrastText: '#0d1117',
    },
    secondary: {
      main: '#718096',
      dark: '#4a5568',
      light: '#a0aec0',
      contrastText: '#0d1117',
    },
    error: {
      main: '#ef5350',
      light: '#3b1515',
    },
    warning: {
      main: '#ffb74d',
      light: '#3e2723',
    },
    success: {
      main: '#66bb6a',
      light: '#1b3a1b',
    },
    info: {
      main: '#42a5f5',
      light: '#1a3a5c',
    },
    background: {
      default: '#0d1117',
      paper: '#1c2433',
    },
    text: {
      primary: '#e2e8f0',
      secondary: '#a0aec0',
      disabled: '#4a5568',
    },
    divider: '#2d3748',
    action: {
      hover: 'rgba(66, 165, 245, 0.08)',
      selected: '#1a3a5c',
      disabled: '#4a5568',
      disabledBackground: '#2d3748',
    },
  },
  typography: {
    fontFamily: "'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    h1: { fontSize: '2rem', fontWeight: 700, lineHeight: 1.2, letterSpacing: '-0.02em' },
    h2: { fontSize: '1.5rem', fontWeight: 700, lineHeight: 1.3, letterSpacing: '-0.01em' },
    h3: { fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.4 },
    h4: { fontSize: '1.125rem', fontWeight: 600, lineHeight: 1.4 },
    h5: { fontSize: '1rem', fontWeight: 600, lineHeight: 1.5 },
    h6: { fontSize: '0.875rem', fontWeight: 600, lineHeight: 1.5, letterSpacing: '0.01em' },
    body1: { fontSize: '1rem', fontWeight: 400, lineHeight: 1.6 },
    body2: { fontSize: '0.875rem', fontWeight: 400, lineHeight: 1.5, letterSpacing: '0.01em' },
    caption: { fontSize: '0.75rem', fontWeight: 500, lineHeight: 1.4, letterSpacing: '0.03em' },
    overline: { fontSize: '0.625rem', fontWeight: 600, lineHeight: 1.6, letterSpacing: '0.08em' },
    button: { fontWeight: 600, letterSpacing: '0.02em', textTransform: 'none' },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#0d1117',
        },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: '#161b22',
          color: '#e2e8f0',
          borderBottom: '1px solid #2d3748',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#161b22',
          color: '#a0aec0',
          borderRight: '1px solid #2d3748',
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 20px',
          fontWeight: 600,
        },
        containedPrimary: {
          '&:hover': { backgroundColor: '#64b5f6' },
        },
        outlinedPrimary: {
          borderColor: '#42a5f5',
          '&:hover': { backgroundColor: '#1a3a5c', borderColor: '#64b5f6' },
        },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid #2d3748',
          backgroundImage: 'none',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 4, fontWeight: 500 },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#2d3748',
            color: '#a0aec0',
            fontWeight: 600,
            fontSize: '0.75rem',
            letterSpacing: '0.03em',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:nth-of-type(even)': { backgroundColor: '#161b22' },
          '&:hover': { backgroundColor: '#1a3a5c' },
        },
      },
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined', size: 'small' },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#2d3748',
          fontSize: '0.75rem',
          borderRadius: 4,
          border: '1px solid #4a5568',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        standardError: { backgroundColor: '#3b1515', color: '#ef5350' },
        standardWarning: { backgroundColor: '#3e2723', color: '#ffb74d' },
        standardSuccess: { backgroundColor: '#1b3a1b', color: '#66bb6a' },
        standardInfo: { backgroundColor: '#1a3a5c', color: '#42a5f5' },
      },
    },
    MuiBox: {
      styleOverrides: {
        root: { boxSizing: 'border-box' },
      },
    },
  },
});
```

## Theme Toggle Pattern

Use React state to switch between themes:

```javascript
import { useState, useMemo } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

function App() {
  const [mode, setMode] = useState('light');

  const theme = useMemo(
    () => (mode === 'light' ? opensarLight : opensarDark),
    [mode]
  );

  const toggleTheme = () => setMode(prev => prev === 'light' ? 'dark' : 'light');

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* Pass toggleTheme to your Header or Settings */}
    </ThemeProvider>
  );
}
```

## Sidebar Active Item

Style active nav items using the brand tokens:

```javascript
// Light mode
const activeItemLight = {
  color: '#1565c0',
  backgroundColor: '#e3f2fd',
  '& .MuiListItemIcon-root': { color: '#1565c0' },
};

// Dark mode
const activeItemDark = {
  color: '#42a5f5',
  backgroundColor: '#1a3a5c',
  '& .MuiListItemIcon-root': { color: '#42a5f5' },
};
```
