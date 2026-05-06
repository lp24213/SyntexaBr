/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./app/**/*.js", "./components/**/*.js"],
  theme: {
    extend: {
      colors: {
        background: "#f8f9fb",
        surface: "#ffffff",
        surfaceMuted: "#f1f5f9",
        borderStrong: "rgba(15,23,42,0.12)",
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
