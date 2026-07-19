/**
 * Central design tokens. Dark, "broadcast console" feel — deep navy with a
 * gridiron-green accent and a warning amber for injuries / risky starts.
 */
export const colors = {
  bg: '#0b0f14',
  bgElevated: '#121822',
  card: '#161e2a',
  cardAlt: '#1b2532',
  border: '#243040',
  text: '#e8eef5',
  textDim: '#9fb0c3',
  textFaint: '#64748b',
  accent: '#31d158', // gridiron green
  accentDim: '#1f7a38',
  blue: '#4c8dff',
  amber: '#f5a623',
  red: '#ff5c5c',
  purple: '#a970ff',
};

/** Position → chip color, matching Sleeper's conventions loosely. */
export const positionColors: Record<string, string> = {
  QB: '#ff6b81',
  RB: '#31d158',
  WR: '#4c8dff',
  TE: '#f5a623',
  K: '#a970ff',
  DEF: '#8b9bb0',
  FLEX: '#c0c8d4',
  DL: '#e0796b',
  LB: '#e0796b',
  DB: '#e0796b',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
};

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  pill: 999,
};

export const font = {
  h1: 26,
  h2: 20,
  h3: 17,
  body: 15,
  small: 13,
  tiny: 11,
};
