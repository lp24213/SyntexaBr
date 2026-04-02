/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.js", "./components/**/*.js"],
  theme: {
    extend: {
      colors: {
        background: "#050506",
        surface: "#111114",
        surfaceMuted: "#0c0c0f",
        borderStrong: "rgba(255,255,255,0.15)",
        primary: "#3b82f6",
        primarySoft: "rgba(59,130,246,0.15)",
        accent: "#3b82f6",
        accentSoft: "rgba(59,130,246,0.15)",
      },
      borderRadius: {
        "2xl": "1.25rem",
        syntexa: "var(--radius-lg, 18px)",
      },
      boxShadow: {
        "soft-xl": "var(--shadow-card)",
        syntexa: "var(--shadow-card)",
      },
    },
  },
  plugins: [],
};
