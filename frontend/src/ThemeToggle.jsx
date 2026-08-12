import { useTheme } from "./ThemeContext";
import { Sun, Moon } from "lucide-react";

export default function ThemeToggle({ size = 16 }) {
  const { theme, toggleTheme, colors } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      id="theme-toggle-btn"
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
      title={`Switch to ${isDark ? "light" : "dark"} theme`}
      style={{
        position: "relative",
        width: "36px",
        height: "36px",
        borderRadius: "10px",
        border: `1px solid ${colors.borderMedium}`,
        background: isDark
          ? "rgba(148,163,184,0.06)"
          : "rgba(250,204,21,0.08)",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        overflow: "hidden",
        flexShrink: 0,
      }}
    >
      <div
        style={{
          position: "absolute",
          transition: "all 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
          transform: isDark
            ? "translateY(0) rotate(0deg)"
            : "translateY(-30px) rotate(-90deg)",
          opacity: isDark ? 1 : 0,
        }}
      >
        <Moon size={size} color="#94a3b8" />
      </div>
      <div
        style={{
          position: "absolute",
          transition: "all 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
          transform: isDark
            ? "translateY(30px) rotate(90deg)"
            : "translateY(0) rotate(0deg)",
          opacity: isDark ? 0 : 1,
        }}
      >
        <Sun size={size} color="#f59e0b" />
      </div>
    </button>
  );
}
