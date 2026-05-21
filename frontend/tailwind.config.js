/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.js", "./components/**/*.js"],
  theme: {
    extend: {
      colors: {
        background: "#f8fafc",
        surface: "#ffffff",
        surfaceMuted: "#f3f4f6",
        borderStrong: "rgba(15,23,42,0.10)",
        primary: "#0f172a",
        primarySoft: "rgba(15,23,42,0.08)",
        accent: "#94a3b8",
        accentSoft: "rgba(148,163,184,0.25)",
      },
      borderRadius: {
        "2xl": "1.25rem",
        syntexa: "var(--radius-lg, 16px)",
      },
      boxShadow: {
        "soft-xl": "var(--shadow-card)",
        syntexa: "var(--shadow-card)",
      },
    },
  },
  plugins: [],
};
