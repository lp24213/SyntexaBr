/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.js", "./components/**/*.js"],
  theme: {
    extend: {
      colors: {
        background: "#fafbfc",
        surface: "#ffffff",
        surfaceMuted: "#f1f2f4",
        borderStrong: "rgba(20,24,30,0.10)",
        primary: "#1a1c1e",
        primarySoft: "rgba(26,28,30,0.08)",
        accent: "#c8cdd4",
        accentSoft: "rgba(200,205,212,0.25)",
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
