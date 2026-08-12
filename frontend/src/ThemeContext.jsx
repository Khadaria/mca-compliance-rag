import { createContext, useContext, useState, useEffect } from "react";

const ThemeContext = createContext();

export const themes = {
  dark: {
    // Backgrounds
    pageBg: "#060d1a",
    cardBg: "rgba(15,23,42,0.7)",
    cardBgSolid: "rgba(15,23,42,0.6)",
    sidebarBg: "rgba(9,16,31,0.8)",
    navBg: "rgba(6,13,26,0.92)",
    navBgSolid: "rgba(6,13,26,0.95)",
    inputBg: "rgba(15,23,42,0.8)",
    inputAreaBg: "rgba(6,13,26,0.9)",
    sourcesPaneBg: "rgba(9,16,31,0.9)",
    hoverBg: "rgba(16,185,129,0.08)",
    quickActionBg: "rgba(15,23,42,0.6)",
    sectionBg: "rgba(15,23,42,0.4)",

    // Borders
    borderSubtle: "rgba(148,163,184,0.08)",
    borderLight: "rgba(148,163,184,0.1)",
    borderMedium: "rgba(148,163,184,0.12)",
    borderInput: "rgba(148,163,184,0.15)",

    // Text
    textPrimary: "#f8fafc",
    textSecondary: "#f1f5f9",
    textBody: "#cbd5e1",
    textMuted: "#94a3b8",
    textDim: "#64748b",
    textDimmer: "#475569",
    textDimmest: "#334155",
    textFaintest: "#1e293b",

    // Accent
    accent: "#10b981",
    accentBg: "rgba(16,185,129,0.08)",
    accentBgStrong: "rgba(16,185,129,0.1)",
    accentBgStronger: "rgba(16,185,129,0.15)",
    accentBorder: "rgba(16,185,129,0.2)",
    accentBorderStrong: "rgba(16,185,129,0.25)",
    accentBorderHover: "rgba(16,185,129,0.3)",

    // Blue accent
    blue: "#0ea5e9",
    blueSoft: "#7dd3fc",
    blueBg: "rgba(14,165,233,0.08)",
    blueBgStrong: "rgba(14,165,233,0.1)",
    blueBorder: "rgba(14,165,233,0.15)",
    blueBorderStrong: "rgba(14,165,233,0.2)",
    blueBorderStronger: "rgba(14,165,233,0.25)",

    // Purple accent
    purple: "#a78bfa",
    purpleBg: "rgba(167,139,250,0.1)",

    // User message
    userMsgBg: "rgba(14,165,233,0.08)",
    userMsgBorder: "rgba(14,165,233,0.15)",
    userMsgText: "#e2e8f0",

    // Source card
    sourceCardBg: "rgba(15,23,42,0.6)",
    sourceCardBorder: "rgba(148,163,184,0.12)",

    // Pipeline info
    pipelineBg: "rgba(15,23,42,0.4)",
    pipelineBorder: "rgba(148,163,184,0.06)",

    // Special
    red: "#ef4444",
    amber: "#f59e0b",
    boldText: "#f1f5f9",
    previewQueryBg: "rgba(16,185,129,0.06)",
    previewQueryBorder: "rgba(16,185,129,0.15)",

    // Markdown renderer
    mdH2: "#f1f5f9",
    mdH3: "#94a3b8",
    mdBlockquoteBorder: "#10b981",
    mdBlockquoteText: "#94a3b8",
    mdBlockquoteBg: "rgba(16,185,129,0.04)",
    mdListText: "#cbd5e1",
    mdBoldText: "#f1f5f9",

    // Scrollbar
    scrollbarThumb: "rgba(148,163,184,0.15)",

    // Skeleton
    skeletonBg: "rgba(148,163,184,0.08)",

    // Step card overlay
    stepArrowBg: "#0f172a",
    stepNumber: "rgba(148,163,184,0.12)",
  },
  light: {
    // Backgrounds
    pageBg: "#f8fafb",
    cardBg: "rgba(255,255,255,0.85)",
    cardBgSolid: "#ffffff",
    sidebarBg: "#f1f5f9",
    navBg: "rgba(255,255,255,0.92)",
    navBgSolid: "rgba(255,255,255,0.95)",
    inputBg: "#ffffff",
    inputAreaBg: "rgba(255,255,255,0.95)",
    sourcesPaneBg: "#f8fafc",
    hoverBg: "rgba(16,185,129,0.06)",
    quickActionBg: "#ffffff",
    sectionBg: "rgba(241,245,249,0.6)",

    // Borders
    borderSubtle: "rgba(148,163,184,0.15)",
    borderLight: "rgba(148,163,184,0.18)",
    borderMedium: "rgba(148,163,184,0.22)",
    borderInput: "rgba(148,163,184,0.3)",

    // Text
    textPrimary: "#0f172a",
    textSecondary: "#1e293b",
    textBody: "#334155",
    textMuted: "#475569",
    textDim: "#64748b",
    textDimmer: "#94a3b8",
    textDimmest: "#94a3b8",
    textFaintest: "#cbd5e1",

    // Accent
    accent: "#059669",
    accentBg: "rgba(5,150,105,0.06)",
    accentBgStrong: "rgba(5,150,105,0.1)",
    accentBgStronger: "rgba(5,150,105,0.14)",
    accentBorder: "rgba(5,150,105,0.2)",
    accentBorderStrong: "rgba(5,150,105,0.3)",
    accentBorderHover: "rgba(5,150,105,0.35)",

    // Blue accent
    blue: "#0284c7",
    blueSoft: "#0284c7",
    blueBg: "rgba(2,132,199,0.06)",
    blueBgStrong: "rgba(2,132,199,0.1)",
    blueBorder: "rgba(2,132,199,0.15)",
    blueBorderStrong: "rgba(2,132,199,0.2)",
    blueBorderStronger: "rgba(2,132,199,0.25)",

    // Purple accent
    purple: "#7c3aed",
    purpleBg: "rgba(124,58,237,0.08)",

    // User message
    userMsgBg: "rgba(2,132,199,0.06)",
    userMsgBorder: "rgba(2,132,199,0.15)",
    userMsgText: "#1e293b",

    // Source card
    sourceCardBg: "#ffffff",
    sourceCardBorder: "rgba(148,163,184,0.2)",

    // Pipeline info
    pipelineBg: "#f1f5f9",
    pipelineBorder: "rgba(148,163,184,0.15)",

    // Special
    red: "#ef4444",
    amber: "#f59e0b",
    boldText: "#0f172a",
    previewQueryBg: "rgba(5,150,105,0.05)",
    previewQueryBorder: "rgba(5,150,105,0.15)",

    // Markdown renderer
    mdH2: "#1e293b",
    mdH3: "#475569",
    mdBlockquoteBorder: "#059669",
    mdBlockquoteText: "#475569",
    mdBlockquoteBg: "rgba(5,150,105,0.04)",
    mdListText: "#334155",
    mdBoldText: "#0f172a",

    // Scrollbar
    scrollbarThumb: "rgba(148,163,184,0.3)",

    // Skeleton
    skeletonBg: "rgba(148,163,184,0.15)",

    // Step card overlay
    stepArrowBg: "#f1f5f9",
    stepNumber: "rgba(148,163,184,0.2)",
  },
};

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("complics-theme");
      return saved === "light" ? "light" : "dark";
    } catch {
      return "dark";
    }
  });

  useEffect(() => {
    localStorage.setItem("complics-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));
  const colors = themes[theme];

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, colors }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
