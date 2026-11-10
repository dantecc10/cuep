import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#A92730",
        "primary-dark": "#851F27",
        secondary: "#4611A0",
        background: "#F8F0EC",
        paper: "#CDB38B",
        "paper-light": "#FFFDFC",
        accent: "#36C6C7",
        text: "#171313",
        yellow: "#E8B83E",
        "red-bright": "#E94B48",
        surface: "#FFFDFC",
        border: "#A92730",
        ink: "#171313",
        cream: "#F8F0EC",
        sand: "#EFE2D4",
        "paper-deep": "#B99A6F",
      },
      fontFamily: {
        display: ["var(--font-display)", "Impact", "sans-serif"],
        editorial: ["var(--font-editorial)", "Georgia", "serif"],
        sans: ["var(--font-body)", "Arial", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "8px",
        button: "4px",
      },
      boxShadow: {
        poster: "6px 6px 0 #DDBFC0",
        "poster-sm": "3px 3px 0 #DDBFC0",
        "poster-ink": "6px 6px 0 #171313",
        lift: "0 18px 40px -24px rgba(23, 19, 19, 0.45)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
