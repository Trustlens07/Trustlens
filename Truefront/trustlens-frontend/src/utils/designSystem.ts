// Design System Tokens
export const designTokens = {
  colors: {
    // Surface colors
    surface: '#faf8ff',
    surfaceDim: '#d9d9e5',
    surfaceBright: '#faf8ff',
    surfaceContainerLowest: '#ffffff',
    surfaceContainerLow: '#f3f3fe',
    surfaceContainer: '#ededf9',
    surfaceContainerHigh: '#e7e7f3',
    surfaceContainerHighest: '#e1e2ed',
    onSurface: '#191b23',
    onSurfaceVariant: '#434655',
    inverseSurface: '#2e3039',
    inverseOnSurface: '#f0f0fb',
    outline: '#737686',
    outlineVariant: '#c3c6d7',
    surfaceTint: '#0053db',

    // Primary colors
    primary: '#004ac6',
    onPrimary: '#ffffff',
    primaryContainer: '#2563eb',
    onPrimaryContainer: '#eeefff',
    inversePrimary: '#b4c5ff',
    primaryFixed: '#dbe1ff',
    primaryFixedDim: '#b4c5ff',
    onPrimaryFixed: '#00174b',
    onPrimaryFixedVariant: '#003ea8',

    // Secondary colors
    secondary: '#505f76',
    onSecondary: '#ffffff',
    secondaryContainer: '#d0e1fb',
    onSecondaryContainer: '#54647a',
    secondaryFixed: '#d3e4fe',
    secondaryFixedDim: '#b7c8e1',
    onSecondaryFixed: '#0b1c30',
    onSecondaryFixedVariant: '#38485d',

    // Tertiary colors
    tertiary: '#943700',
    onTertiary: '#ffffff',
    tertiaryContainer: '#bc4800',
    onTertiaryContainer: '#ffede6',
    tertiaryFixed: '#ffdbcd',
    tertiaryFixedDim: '#ffb596',
    onTertiaryFixed: '#360f00',
    onTertiaryFixedVariant: '#7d2d00',

    // Error colors
    error: '#ba1a1a',
    onError: '#ffffff',
    errorContainer: '#ffdad6',
    onErrorContainer: '#93000a',

    // Background
    background: '#faf8ff',
    onBackground: '#191b23',
    surfaceVariant: '#e1e2ed',
  },

  typography: {
    metricXl: {
      fontFamily: 'Inter',
      fontSize: '32px',
      fontWeight: '700',
      lineHeight: '1.2',
    },
    metricLg: {
      fontFamily: 'Inter',
      fontSize: '24px',
      fontWeight: '700',
      lineHeight: '1.2',
    },
    headingLg: {
      fontFamily: 'Inter',
      fontSize: '24px',
      fontWeight: '600',
      lineHeight: '32px',
    },
    headingMd: {
      fontFamily: 'Inter',
      fontSize: '20px',
      fontWeight: '600',
      lineHeight: '28px',
    },
    headingSm: {
      fontFamily: 'Inter',
      fontSize: '18px',
      fontWeight: '600',
      lineHeight: '26px',
    },
    body: {
      fontFamily: 'Inter',
      fontSize: '14px',
      fontWeight: '400',
      lineHeight: '20px',
    },
    label: {
      fontFamily: 'Inter',
      fontSize: '12px',
      fontWeight: '500',
      lineHeight: '16px',
    },
  },

  spacing: {
    base: '8px',
    xs: '4px',
    sm: '12px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    gutter: '24px',
    margin: '32px',
  },

  borderRadius: {
    sm: '0.25rem',
    default: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
    xl: '1.5rem',
    full: '9999px',
  },

  shadows: {
    low: '0px 1px 3px rgba(30, 41, 59, 0.05)',
    mid: '0px 4px 6px rgba(30, 41, 59, 0.08)',
    high: '0px 10px 15px rgba(30, 41, 59, 0.1)',
  },
}

// Utility functions for common design patterns
export const getStatusColor = (status: 'success' | 'warning' | 'error') => {
  const colors = {
    success: designTokens.colors.primary,
    warning: designTokens.colors.tertiary,
    error: designTokens.colors.error,
  }
  return colors[status]
}

export const getStatusBgColor = (status: 'success' | 'warning' | 'error') => {
  const colors = {
    success: `${designTokens.colors.primary}10`, // 10% opacity
    warning: `${designTokens.colors.tertiary}10`,
    error: `${designTokens.colors.error}10`,
  }
  return colors[status]
}