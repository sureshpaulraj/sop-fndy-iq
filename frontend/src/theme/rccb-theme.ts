/** Contoso Design Tokens — Reyes Coca-Cola Bottling Brand Theme */

export const ContosoTheme = {
  colors: {
    primary: '#F40009',       // Coca-Cola Red
    primaryHover: '#D10007',
    dark: '#1A1A1A',
    darkSecondary: '#2D2D2D',
    white: '#FFFFFF',
    gray100: '#F5F5F5',       // Chat background
    gray200: '#E5E7EB',
    gray300: '#D1D5DB',       // Borders
    gray500: '#6B7280',       // Secondary text
    gray700: '#374151',
    green: '#10B981',         // Positive feedback
    blue: '#3B82F6',          // Citations
    blueLight: '#EFF6FF',     // Citation hover
    red: '#EF4444',           // Errors
    redLight: '#FEF2F2',      // Error background
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontMono: "'JetBrains Mono', 'Fira Code', monospace",
    h1: { size: '24px', weight: 700, lineHeight: '32px' },
    h2: { size: '20px', weight: 600, lineHeight: '28px' },
    body: { size: '14px', weight: 400, lineHeight: '20px' },
    message: { size: '15px', weight: 400, lineHeight: '24px' },
    citation: { size: '12px', weight: 500, lineHeight: '16px' },
    code: { size: '13px', weight: 400, lineHeight: '20px' },
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px rgba(0,0,0,0.05)',
    md: '0 4px 6px rgba(0,0,0,0.07)',
    lg: '0 10px 15px rgba(0,0,0,0.1)',
  },
  layout: {
    sidebarWidth: '240px',
    citationPanelWidth: '280px',
    headerHeight: '56px',
    maxChatWidth: '800px',
  },
} as const;

export type ContosoTheme = typeof ContosoTheme;
