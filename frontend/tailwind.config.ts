import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // charcoal surface scale
        ink: {
          950: "#0a0c11",
          900: "#0f131a",
          850: "#141923",
          800: "#1b2230",
          700: "#273142",
          600: "#3b475c",
        },
        // lime/emerald accent
        accent: {
          DEFAULT: "#a3e635",
          soft: "#bef264",
          dim: "#4d7c0f",
        },
      },
      fontFamily: {
        sans: ["var(--font-display)", "var(--font-arabic)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-arabic)", "sans-serif"],
        arabic: ["var(--font-arabic)", "var(--font-display)", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
