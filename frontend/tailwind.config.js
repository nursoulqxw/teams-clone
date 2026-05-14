/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        teams: {
          purple: "#6264A7",
          "purple-dark": "#464775",
          "purple-light": "#8B8CC7",
          sidebar: "#201F1F",
          "sidebar-hover": "#2D2C2C",
          content: "#F3F2F1",
          border: "#E1DFDD",
        },
      },
    },
  },
  plugins: [],
};
