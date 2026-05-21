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
          950: "#002A32",
          900: "#00333D",
          800: "#00414D"
        },
        neon: {
          crimson: "#ED254E",
          teal: "#ED254E",
          amber: "#ED254E",
          ice: "#d8dee9"
        },
        brand: {
          base: "#002A32",
          accent: "#ED254E"
        }
      },
      boxShadow: {
        "neon-crimson": "0 0 32px rgba(237, 37, 78, 0.34)",
        "neon-teal": "0 0 32px rgba(237, 37, 78, 0.28)"
      }
    }
  },
  plugins: []
};

export default config;
