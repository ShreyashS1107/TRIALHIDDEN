import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: 'class',
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#040d13",
          900: "#06131C",
          850: "#081A24",
          800: "#0B202B",
          750: "#0F2A38",
          700: "#133547",
        },
        cyan: {
          DEFAULT: "#39D9FF",
          glow: "rgba(57, 217, 255, 0.4)",
          subtle: "rgba(57, 217, 255, 0.12)",
          border: "rgba(57, 217, 255, 0.25)",
        },
        teal: {
          DEFAULT: "#27C7B8",
          subtle: "rgba(39, 199, 184, 0.15)",
        },
        amber: {
          DEFAULT: "#F4B942",
          subtle: "rgba(244, 185, 66, 0.15)",
          border: "rgba(244, 185, 66, 0.35)",
        },
        critical: {
          DEFAULT: "#FF5C5C",
          subtle: "rgba(255, 92, 92, 0.15)",
          border: "rgba(255, 92, 92, 0.35)",
        },
        healthy: {
          DEFAULT: "#22C55E",
          subtle: "rgba(34, 197, 94, 0.15)",
        },
        concrete: {
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
        }
      },
      fontFamily: {
        sans: ["var(--font-jakarta)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(57, 217, 255, 0.25)",
        "glow-amber": "0 0 25px -5px rgba(244, 185, 66, 0.25)",
        "glow-critical": "0 0 25px -5px rgba(255, 92, 92, 0.25)",
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "ping-slow": "ping 2.5s cubic-bezier(0, 0, 0.2, 1) infinite",
      }
    },
  },
  plugins: [],
};

export default config;
