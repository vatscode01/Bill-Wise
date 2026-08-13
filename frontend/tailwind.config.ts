import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe6fe",
          500: "#4361ee",
          600: "#3651d4",
          700: "#2c41ab",
        },
      },
    },
  },
  plugins: [],
};
export default config;
