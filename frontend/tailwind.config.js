/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas:      "#0c0b0a",
        panel:       "#15130f",
        "panel-2":   "#191610",
        raised:      "#201d17",
        "raised-hi": "#2a261e",
        hairline:    "rgba(231,221,205,0.09)",
        "hairline-2":"rgba(231,221,205,0.15)",
        ink: {
          100: "#efeae1",
          300: "#b8b0a4",
          500: "#847d70",
          600: "#6a6358",
        },
        copper: {
          300: "#e8b486",
          400: "#d28f5c",
          500: "#b8763f",
        },
        sage: {
          300: "#9fdcb6",
          400: "#6db78a",
          950: "#13231a",
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', "system-ui", "sans-serif"],
        sans:    ['"Hanken Grotesk"', "system-ui", "sans-serif"],
        mono:    ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      borderRadius: {
        panel:   "16px",
        control: "10px",
        tile:    "12px",
      },
      boxShadow: {
        panel:   "0 1px 0 0 rgba(231,221,205,0.05) inset, 0 24px 50px -28px rgba(0,0,0,0.85)",
        control: "0 1px 0 0 rgba(231,221,205,0.05) inset, 0 1px 2px rgba(0,0,0,0.4)",
        glow:    "0 0 0 1px #d28f5c, 0 8px 20px -10px rgba(210,143,92,0.45)",
        cta:     "0 1px 0 0 rgba(231,221,205,0.05) inset, 0 10px 24px -10px rgba(210,143,92,0.55)",
      },
    },
  },
  plugins: [],
};
