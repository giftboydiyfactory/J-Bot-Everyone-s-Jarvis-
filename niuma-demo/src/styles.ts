// Shared design tokens for J-Bot demo video

export const COLORS = {
  // Background colors
  bgPrimary: "#1a1a2e",
  bgSecondary: "#16213e",
  bgTertiary: "#0f3460",

  // Teams-inspired colors
  teamsBg: "#292b3d",
  teamsPanel: "#1f2133",
  teamsBorder: "#3a3d52",
  teamsHover: "#3a3d52",
  teamsMessage: "#2d2f3e",
  teamsUserBubble: "#4a4fc7",

  // Accent colors
  nvidiaGreen: "#76B900",
  nvidiaGreenDark: "#5a8c00",
  nvidiaGreenLight: "#8fd400",
  nvidiaGlow: "rgba(118, 185, 0, 0.3)",

  // Text colors
  textPrimary: "#ffffff",
  textSecondary: "#b3b3b3",
  textMuted: "#6e6e6e",
  textGreen: "#76B900",

  // Status colors
  statusSuccess: "#3fb950",
  statusWarning: "#d29922",
  statusError: "#f85149",
  statusInfo: "#2196f3",

  // Terminal
  terminalBg: "#0d1117",
  terminalText: "#e6edf3",
  terminalGreen: "#3fb950",
  terminalYellow: "#d29922",
  terminalBlue: "#79c0ff",
  terminalGray: "#8b949e",

  // Special
  avatarBot: "#76B900",
  avatarUser1: "#4a4fc7",
  avatarUser2: "#9c27b0",
  avatarUser3: "#ff5722",
  avatarUser4: "#00bcd4",
  highlight: "rgba(118, 185, 0, 0.15)",
};

export const FONTS = {
  title: "700 72px 'Segoe UI', system-ui, sans-serif",
  subtitle: "400 36px 'Segoe UI', system-ui, sans-serif",
  heading: "700 48px 'Segoe UI', system-ui, sans-serif",
  body: "400 24px 'Segoe UI', system-ui, sans-serif",
  code: "400 18px 'Consolas', 'Courier New', monospace",
  small: "400 18px 'Segoe UI', system-ui, sans-serif",
  teamsName: "600 15px 'Segoe UI', system-ui, sans-serif",
  teamsBody: "400 15px 'Segoe UI', system-ui, sans-serif",
  teamsMeta: "400 12px 'Segoe UI', system-ui, sans-serif",
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const SCENE_DURATIONS = {
  title: 90,
  problem: 180,
  solution: 150,
  liveDemo: 450,
  architecture: 300,
  features: 360,
  multiUser: 360,
  easterEgg: 240,
  outro: 90,
};

export const TOTAL_FRAMES = Object.values(SCENE_DURATIONS).reduce(
  (sum, d) => sum + d,
  0
);

export const FPS = 30;
