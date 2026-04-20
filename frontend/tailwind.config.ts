import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./stores/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#070910",
          900: "#0b1020",
          800: "#111827"
        },
        neon: {
          crimson: "#ff385c",
          teal: "#14b8a6",
          amber: "#f97316",
          ice: "#d8dee9"
        }
      },
      boxShadow: {
        "neon-crimson": "0 0 32px rgba(255, 56, 92, 0.34)",
        "neon-teal": "0 0 32px rgba(20, 184, 166, 0.28)"
      }
    }
  },
  plugins: []
};

export default config;
