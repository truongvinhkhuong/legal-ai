import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#e8f4f8",
          100: "#c5e3ed",
          200: "#9fd0e1",
          300: "#6db9d2",
          400: "#34a1c3",
          500: "#016494",
          600: "#015a85",
          700: "#014f76",
          800: "#014567",
          900: "#013a58",
        },
      },
    },
  },
  plugins: [typography],
};

export default config;
